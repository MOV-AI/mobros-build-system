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


def is_ros_package(name):
    """function that checks if a package is a ros package. UNUSED"""
    return name.startswith("ros-")


class InstallRuntimeDependsExecuter:
    """Executor responsible for producing ros/ros-movai packages in a ros workspace."""

    def __init__(self):
        """If your executor requires some initialization, use the class constructor for it"""
        logging.debug("[RosInstallDepExecuter] init")

    #pylint: disable=R0915,R0914,R1702,R0912
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
        user_requested_packages={}
        for pkg_input_data in install_pkgs:
            version = ""
            name = pkg_input_data
            if "=" in pkg_input_data:
                name, version = pkg_input_data.split("=")

            if not apt_utils.is_virtual_package(name):
                user_requested_packages[name]=version
                dependency_manager.register_root_package(name, version, "user")
                #package = DebianPackage(pkg_name, user_requested_packages[pkg_name], args.upgrade_installed)
                #package = DebianPackage(name, version, args.upgrade_installed)
                #dependency_manager.register_package(package, args.upgrade_installed)
            else:
                logging.warning("Package: " + name + " is a virtual package. Skipping")

        for pkg_name in user_requested_packages:
            package = DebianPackage(pkg_name, user_requested_packages[pkg_name], args.upgrade_installed)
            dependency_manager.register_package(package, args.upgrade_installed)


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
                            package_to_inspect["name"], package_to_inspect["version"], args.upgrade_installed 
                        )

                        if package_to_inspect["name"] not in user_requested_packages:
                            installed_package_version = (
                                apt_utils.get_package_installed_version(package_to_inspect["name"])
                            )
                            if installed_package_version:
                                if args.upgrade_installed or package_to_inspect["name"] not in user_requested_packages:
                                    
                                    dependency_manager.register_root_package(
                                        package_to_inspect["name"], installed_package_version, "Installed"
                                    )

                        dependency_manager.register_package(
                            package, args.upgrade_installed
                        )

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


        dependency_manager.render_tree()

        install_queue = queue.LifoQueue()
        known_packages = {}
        for tree_level in LevelOrderGroupIter(dependency_manager.root):
            for elem in tree_level:
                if elem.name not in known_packages:
                    if dependency_manager.has_candidate_calculated(elem.name):

                        install_queue.put(elem.name)
                        known_packages[elem.name] = None

        start1 = time.time()
        package_list = ""
        while not install_queue.empty():
            deb_name = install_queue.get()
            if deb_name in ("/","unidentified"):
                continue

            version = dependency_manager.get_version_of_candidate(deb_name)
            if not apt_utils.is_package_already_installed(deb_name, version):
                is_installed = apt_utils.is_package_already_installed(deb_name)
                if args.upgrade_installed or dependency_manager.is_user_requested_package(deb_name) or not apt_utils.is_package_already_installed(deb_name, version):
                    if is_installed:
                        logging.userWarning(
                            "Installing " + deb_name + "=" + version + " (Upgrading from "+apt_utils.get_package_installed_version(deb_name)+")"
                        )
                    else:
                        logging.userInfo("Installing " + deb_name + "=" + version)

                    package_list += deb_name + "=" + version + "\n"

        if package_list == "":
            logging.userInfo(
                "Mobros install Nothing to do. Everything is in the expected version!"
            )
            sys.exit(0)

        if not args.y:
            val = input("You want to continue? (y/n): ")
            if val.lower() not in ["y", "yes"]:
                logging.warning("Aborting.")
                sys.exit(1)

        write_to_file("packages.apt", package_list)

        apt_utils.execute_shell_command(
            "/usr/bin/apt install $(cat packages.apt) -y --allow-downgrades",
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
