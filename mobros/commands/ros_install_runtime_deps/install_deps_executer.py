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
from mobros.utils.utilitary import write_to_file


def register_dependency_tree_roots(install_pkgs, dependency_manager, upgrade_installed):
    """Register the user requested packages as roots of the tree

    Args:
        install_pkgs (str []): array of string with package and version seperated by '=' just like in apt.
        dependency_manager (DependencyManager): Dependency manager instance to used through out the process.
        upgrade_installed (boolean): true if should upgrade all the installed packages the tree touches.
    """
    user_requested_packages = {}
    for pkg_input_data in install_pkgs:
        version = ""
        name = pkg_input_data
        if "=" in pkg_input_data:
            name, version = pkg_input_data.split("=")

        if not apt_utils.is_virtual_package(name):
            user_requested_packages[name] = version
            dependency_manager.register_root_package(name, version, "user")

        else:
            logging.warning("Package: " + name + " is a virtual package. Skipping")

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


def calculate_install_order(dependency_manager, upgrade_installed):
    """Iterates over the dependencies throught the dependency tree, and calculates candidates for them all.

    Args:
        dependency_manager (DependencyManager): Dependency manager instance to used through out the process.
        upgrade_installed (boolean): true if should upgrade all the installed packages the tree touches.

    Returns:
        str: Ordered packages to install seperated by 'new line'
    """

    install_queue = queue.LifoQueue()
    known_packages = {}
    for tree_level in LevelOrderGroupIter(dependency_manager.root):
        for elem in tree_level:
            if elem.name not in known_packages:
                if dependency_manager.has_candidate_calculated(elem.name):
                    install_queue.put(elem.name)
                    known_packages[elem.name] = None

    package_list = ""
    while not install_queue.empty():
        deb_name = install_queue.get()
        if deb_name in ("/", "unidentified"):
            continue

        version = dependency_manager.get_version_of_candidate(deb_name)
        if not apt_utils.is_package_already_installed(deb_name, version):
            is_installed = apt_utils.is_package_already_installed(deb_name)
            if (
                upgrade_installed
                or dependency_manager.is_user_requested_package(deb_name)
                or not apt_utils.is_package_already_installed(deb_name, version)
            ):
                if is_installed:
                    logging.userWarning(
                        "Installing "
                        + deb_name
                        + "="
                        + version
                        + " (Upgrading from "
                        + apt_utils.get_package_installed_version(deb_name)
                        + ")"
                    )
                else:
                    logging.userInfo("Installing " + deb_name + "=" + version)

                package_list += deb_name + "=" + version + "\n"
    return package_list


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
        if not install_pkgs:
            logging.userInfo("No packages mentioned. Nothing todo.")
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

        ordered_package_list = calculate_install_order(
            dependency_manager, args.upgrade_installed
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

        apt_utils.execute_shell_command(
            "/usr/bin/apt-get install $(cat packages.apt) -y --allow-downgrades --no-install-recommends",
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
            "--pkg_list",
            required=False,
            type=str,
            nargs="+",
            default=[],
        )
        parser.add_argument(
            "--upgrade-installed",
            required=False,
            action="store_true",
            dest="upgrade_installed",
        )
