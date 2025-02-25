"""Module responsible for packaging all ros components in a workspace"""

import os
import queue
import sys
import time

from anytree import LevelOrderGroupIter

import mobros.utils.logger as logging
from mobros.commands.ros_install_runtime_deps.debian_package import DebianPackage
from mobros.dependency_manager.dependency_manager import DependencyManager
from mobros.utils import apt_utils
from mobros.utils.utilitary import write_to_file, deep_copy_object
from mobros.commands.ros_install_runtime_deps.install_list_handler import (
    InstallListHandler,
)
from mobros.types.mobros_global_data import GlobalData
from mobros.types.apt_cache_singleton import AptCache
from mobros.exceptions import AptCacheInitializationException
from mobros.constants import Commands


def check_if_requested_packages_are_in_desired_state(install_pkgs):
    """Quick check if the requested packages are already in the desired state

    Args:
        install_pkgs (str []): array of string with package and version seperated by '=' just like in apt.

    Returns:
        boolean: Returns True if packages(all) are already in the desired state, False otherwise.
    """
    for pkg_input_data in install_pkgs:
        version = ""
        name = pkg_input_data
        if "=" in pkg_input_data:
            name, version = pkg_input_data.split("=")

        if version == "":
            if apt_utils.is_package_already_installed(name):
                logging.warning(
                    "Skipping the inputed package "
                    + name
                    + ". Its already Installed. If you want to force it, specify a version!"
                )
                continue

            return False

        if not apt_utils.is_virtual_package(name):
            if not apt_utils.is_package_already_installed(name, version):
                return False
        else:
            logging.warning(
                "Package: "
                + name
                + " is a virtual package. Do not input virtual packages! Skipping!"
            )

    return True


def register_dependency_tree_roots(install_pkgs, dependency_manager, upgrade_installed):
    """Register the user requested packages as roots of the tree

    Args:
        install_pkgs (str []): array of string with package and version seperated by '=' just like in apt.
        dependency_manager (DependencyManager): Dependency manager instance to used through out the process.
        upgrade_installed (boolean): true if should upgrade all the installed packages the tree touches.
    """
    user_requested_packages = {}
    g_data = GlobalData()
    for pkg_input_data in install_pkgs:
        version = ""
        name = pkg_input_data
        if "=" in pkg_input_data:
            name, version = pkg_input_data.split("=")

        if not apt_utils.is_virtual_package(name):
            user_requested_packages[name] = version
            package_name = name
            if apt_utils.is_package_local_file(name):
                package_name, version = apt_utils.get_local_deb_name_version(name)
                dependency_manager.register_local_package(name, package_name, version)

            dependency_manager.register_root_package(package_name, version, "user")
            g_data.set_user_package(package_name, version)

        else:
            logging.warning(
                "Package: "
                + name
                + " is a virtual package. Do not input virtual packages! Skipping!"
            )

    for pkg_name, pkg_version in user_requested_packages.items():
        package = DebianPackage(pkg_name, pkg_version, upgrade_installed)
        dependency_manager.register_package(package, upgrade_installed)


def fill_and_calculate_dependency_tree(dependency_manager, upgrade_installed):
    """Iterates over the dependencies throught the dependency tree, and calculates candidates for them all.

    Args:
        dependency_manager (DependencyManager): Dependency manager instance to used through out the process.
        upgrade_installed (boolean): true if should upgrade all the installed packages the tree touches.
    """
    first_tree_level = True
    packages_uninspected = []
    known_packages = {}

    while len(packages_uninspected) > 0 or first_tree_level:
        if first_tree_level:
            first_tree_level = False

        else:

            for package_to_inspect in packages_uninspected:
                if not apt_utils.is_virtual_package(package_to_inspect["name"]):
                    if not dependency_manager.is_local_package(
                        package_to_inspect["name"] + "=" + package_to_inspect["version"]
                    ):
                        package = DebianPackage(
                            package_to_inspect["name"],
                            package_to_inspect["version"],
                            upgrade_installed,
                        )
                        dependency_manager.register_package(package, upgrade_installed)

                else:
                    logging.debug(
                        "Package: "
                        + package_to_inspect["name"]
                        + " is a virtual package. Skipping"
                    )

        dependency_manager.check_colisions()
        dependency_manager.calculate_installs()
        install_list = dependency_manager.get_install_list()

        packages_uninspected = []

        for candidate in install_list:
            if (
                candidate["name"] not in known_packages
                or candidate["version"] != known_packages[candidate["name"]]
            ):
                known_packages[candidate["name"]] = candidate["version"]
                packages_uninspected.append(candidate)


def fill_install_queue(dependency_manager, known_packages, clean_requested_pkgs):
    """Fill installation queue with the calculated candidates

    Args:
        dependency_manager (dependency_manager): dependency manager object
        known_packages (map): Known of evaluated packages
        clean_requested_pkgs (list): List of requested packages by the user. Name only.

    Returns:
        queue: Ordered queue with priotization taken in consideration
    """
    install_queue = queue.PriorityQueue()
    tree_level_id = 0
    for tree_level in LevelOrderGroupIter(dependency_manager.root):
        tree_level_id += 1
        for elem in tree_level:

            if elem.name not in known_packages:
                if dependency_manager.has_candidate_calculated(elem.name):
                    curr_id = tree_level_id
                    if elem.name in clean_requested_pkgs:
                        curr_id += clean_requested_pkgs.index(elem.name) * 0.1
                    install_queue.put((curr_id, elem.name))
                    known_packages[elem.name] = None
    return install_queue


def fill_list_handler(
    list_handler,
    dependency_manager,
    clean_requested_pkgs,
    ordered_requested_pkgs,
    independent_requested_pkgs,
):
    """Fill the list handler with a ordered list of packages to be installed

    Args:
        list_handler (InstallListHandler): Handler of installation list for apt
        dependency_manager (dependency_manager): dependency manager object
        clean_requested_pkgs (list): List of requested packages by the user. Name only.
        ordered_requested_pkgs (Queue): Queue of requested packages by the user reversed. Name only.
        independent_requested_pkgs (list): List of requested packages by the user that noone depends of.
    """
    known_packages = {}
    install_queue = fill_install_queue(
        dependency_manager, known_packages, clean_requested_pkgs
    )

    if not ordered_requested_pkgs.empty():
        current_requested = ordered_requested_pkgs.get()
    else:
        current_requested = None

    # Pre install queue poping.
    while current_requested in independent_requested_pkgs:

        deb_name = current_requested
        if dependency_manager.has_candidate_calculated(deb_name):
            version = dependency_manager.get_version_of_candidate(deb_name)
            list_handler.register_ordered_element(deb_name, version)
        known_packages[current_requested] = None
        if not ordered_requested_pkgs.empty():
            current_requested = ordered_requested_pkgs.get()
        else:
            current_requested = None

    # Installation queue poping
    while not install_queue.empty():
        deb_name = install_queue.get()[1]

        if deb_name not in independent_requested_pkgs:
            known_packages[deb_name] = None
            if deb_name in ("/", "unidentified"):
                continue
            version = dependency_manager.get_version_of_candidate(deb_name)
            list_handler.register_ordered_element(deb_name, version)

    # Post install queue poping.
    while not ordered_requested_pkgs.empty():
        deb_name = ordered_requested_pkgs.get()
        if deb_name in independent_requested_pkgs:
            version = dependency_manager.get_version_of_candidate(deb_name)
            list_handler.register_ordered_element(deb_name, version)

    # Process items that disapeared from the dependency tree
    # TODO in the future try to understand why they disapeared. Might be the conflict solver
    for e in dependency_manager.install_candidates:
        if e not in known_packages:
            list_handler.register_ordered_element(e, dependency_manager.get_version_of_candidate(e))

def calculate_install_order(dependency_manager, upgrade_installed, request_pkg_order):
    """Iterates over the dependencies throught the dependency tree, and calculates candidates for them all.

    Args:
        dependency_manager (DependencyManager): Dependency manager instance to used through out the process.
        upgrade_installed (boolean): true if should upgrade all the installed packages the tree touches.

    Returns:
        str: Ordered packages to install seperated by 'new line'
    """
    independent_requested_pkgs = []
    ordered_requested_pkgs = queue.LifoQueue()
    clean_requested_pkgs = []

    pkg_list = deep_copy_object(request_pkg_order)
    # pkg_list.reverse()

    for pkg in pkg_list:
        package_name = ""
        version = ""

        if apt_utils.is_package_local_file(pkg):
            package_name, version = apt_utils.get_local_deb_name_version(pkg)
        else:
            if "=" in pkg:
                package_name = pkg.split("=")[0]
                version = pkg.split("=")[1]
            else:
                package_name = pkg
                # logging.error("Package: " + pkg + " has no version specified!")
                if apt_utils.is_virtual_package(pkg):
                    continue
                version = apt_utils.get_package_available_versions(pkg)[0]

        if apt_utils.is_virtual_package(pkg):
            continue
        clean_requested_pkgs.append(package_name)
        ordered_requested_pkgs.put(package_name)

        for dep_name, version_rules in dependency_manager.dependency_bank.items():
            if (
                dep_name == package_name
                and len(version_rules) == 1
                and version_rules[0]["from"] == "user"
            ):
                if not dependency_manager.check_if_any_depends_on(
                    package_name, version
                ):
                    independent_requested_pkgs.append(package_name)
                    break

    list_handler = InstallListHandler(upgrade_installed, dependency_manager)

    fill_list_handler(
        list_handler,
        dependency_manager,
        clean_requested_pkgs,
        ordered_requested_pkgs,
        independent_requested_pkgs,
    )

    list_handler.print_installation_report()

    return (
        list_handler.get_package_list_as_string(),
        list_handler.get_package_auto_list_as_string(),
        list_handler.get_package_hold_list_as_string(),
    )


def is_ros_package(name):
    """function that checks if a package is a ros package. UNUSED"""
    return name.startswith("ros-")


# def reset_apt_cache(mob_cache):
#     cache = apt_utils.AptCache().get_cache()
#     cache.open()
#     for pkg_name, version in mob_cache.items():
#         pkg = cache.get(pkg_name)
#         candidate= pkg.versions.get(version)
#         pkg.candidate=candidate
#         pkg.mark_install()


class InstallRuntimeDependsExecuter:
    """Executor responsible for producing ros/ros-movai packages in a ros workspace."""

    def __init__(self):
        """If your executor requires some initialization, use the class constructor for it"""
        logging.debug("[RosInstallDepExecuter] init")

    # pylint: disable=R0915,R0914,R1702,R0912
    def execute(self, args):
        """Method where the main behaviour of the executer should be"""
        logging.debug("[RosInstallDepExecuter] execute. Args received: " + str(args))

        if os.getuid() != 0:
            logging.error(
                "This command requires sudo to be able to install the dependencies."
            )
            sys.exit(1)

        install_pkgs = args.pkg_list
        if Commands.INSTALL.value in install_pkgs:
            install_pkgs.remove(Commands.INSTALL.value)

        if not install_pkgs:
            logging.userInfo("No packages mentioned. Nothing todo.")
            sys.exit(0)

        try:
            AptCache()
        except AptCacheInitializationException:
            if not args.fail_on_apt_update:
                input_val = input(
                    "You want to proceed with your outdated cache? (y/n): "
                )
                if input_val.lower() not in ["y", "yes"]:
                    sys.exit(1)
            else:
                sys.exit(1)

        if check_if_requested_packages_are_in_desired_state(install_pkgs):
            logging.userInfo(
                "Mobros install has nothing to do. Everything is in the expected version!"
            )
            sys.exit(0)

        dependency_manager = DependencyManager()

        # pkgs_skipped={}
        # mob_cache={}
        # with apt_utils.AptCache().get_cache().actiongroup():

        #     for pkg_input_data in install_pkgs:
        #         version = ""
        #         name = pkg_input_data
        #         if "=" in pkg_input_data:
        #             name, version = pkg_input_data.split("=")

        #         pkg = apt_utils.AptCache().get_cache().get(name)
        #         if version != "":

        #             candidate= pkg.versions.get(version)
        #             pkg.candidate = pkg.versions.get(candidate)

        #         before=apt_utils.AptCache().get_cache().install_count
        #         pkg.mark_install()
        #         if (before == apt_utils.AptCache().get_cache().install_count):
        #             pkgs_skipped[name]=version
        #             check_deps(name, version, pkgs_skipped, mob_cache)
        #         else:
        #             mob_cache[name]=version

        #         print("reiterar os falhados ------------------------------")
        #         for i_name, vers in pkgs_skipped.items():
        #             print("retrying skipped "+i_name+ "="+vers)
        #             # pkg = cache.get(i_name)
        #             # candidate= pkg.versions.get(vers)
        #             # #candidate= pkg.versions.get(version)

        #             # pkg.candidate = candidate
        #             # print("dependency analyu"+str(cache.install_count))

        #             # pkg.mark_install()
        #         print("back to parent")
        #         pkg = apt_utils.AptCache().get_cache().get(name)
        #         if version != "":
        #             print ("is "+version+" in "+str(pkg.versions))
        #             candidate= pkg.versions.get(version)
        #             print(candidate)
        #             pkg.candidate = pkg.versions.get(candidate)
        #         else:
        #             print("l")
        #         before=apt_utils.AptCache().get_cache().install_count
        #         pkg.mark_install()
        #         if (before == apt_utils.AptCache().get_cache().install_count):
        #             print(" ainda nao consigo ???????")
        #             #sys.exit(1)
        #         apt_utils.AptCache().get_cache().commit()
        #         print("end")
        #         apt_utils.AptCache().get_cache().close()

        # sys.exit(1)

        register_dependency_tree_roots(
            install_pkgs, dependency_manager, args.upgrade_installed
        )

        fill_and_calculate_dependency_tree(dependency_manager, args.upgrade_installed)

        dependency_manager.render_tree()
        start1 = time.time()

        ordered_package_list, package_list_mark_auto, package_list_mark_hold = (
            calculate_install_order(
                dependency_manager, args.upgrade_installed, install_pkgs
            )
        )

        if ordered_package_list == "":
            logging.userInfo(
                "Mobros install has nothing to do. Everything is in the expected version!"
            )
            sys.exit(0)

        if not args.y:
            val = input("You want to continue? (y/n): ")
            if val.lower() not in ["y", "yes"]:
                logging.warning("Aborting.")
                sys.exit(1)

        write_to_file("packages.apt", ordered_package_list)
        write_to_file("packages_auto.apt", package_list_mark_auto)
        write_to_file("packages_hold.apt", package_list_mark_hold)

        apt_utils.execute_shell_command(
            '/usr/bin/apt-get install $(cat packages.apt) -y '\
                '--allow-downgrades '\
                '--no-install-recommends '\
                '--no-install-suggests '\
                '--allow-change-held-packages',
            stop_on_error=True,
            log_output=True,
            shell_mode=True,
        )

        apt_utils.execute_shell_command(
            "/usr/bin/apt-mark hold $(cat packages_hold.apt)",
            stop_on_error=True,
            log_output=True,
            shell_mode=True,
        )

        if package_list_mark_auto != "":
            apt_utils.execute_shell_command(
                "/usr/bin/apt-mark auto $(cat packages_auto.apt)",
                stop_on_error=True,
                log_output=True,
                shell_mode=True,
            )

        end1 = time.time()

        logging.debug("Installation took: " + str(end1 - start1))
        logging.userInfo("Mobros install Successfull!")

    @staticmethod
    def add_expected_arguments(parser):
        """Method exposed for the handle to append our executer arguments."""
        parser.add_argument(
            "pkg_list",
            type=str,
            nargs="+",
            default=[],
            help="List of packages to be installed, just like apt. It can contain the specific version of it <name>=<version>",
        )
        parser.add_argument(
            "--upgrade-installed",
            required=False,
            action="store_true",
            dest="upgrade_installed",
            help="Don't mind the versions that are installed, use the latest available in apt cache.",
        )
        parser.add_argument(
            "-y",
            required=False,
            action="store_true",
            help="Consider yes for any confirmation.",
        )
        parser.add_argument(
            "--fail-on-apt-update",
            action="store_true",
            help="Ensure mobros uses an updated apt cache. If it fails, it will exit with error.",
        )
        return [parser.parse_args(), None]

    @staticmethod
    def get_description():
        """Method exposed to allow the handler to describe the command in the call of help"""
        return "Command responsible for installing apt packages. It wraps and enhances apt due to his limitations on dealing with dependency trees and using specific versions of dependencies"
