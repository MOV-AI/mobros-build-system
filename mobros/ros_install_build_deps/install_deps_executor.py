"""Module responsible for packaging all ros components in a workspace"""
import os
import sys

import mobros.utils.logger as logging
from mobros.ros_install_build_deps.catkin_package_manager import (
    CatkinPackage,
    is_catkin_blacklisted,
)
from mobros.ros_install_build_deps.dependency_manager import DependencyManager
from mobros.utils.apt_utils import install_package


class InstallBuildDependsExecutor:
    """Executor responsible for producing ros/ros-movai packages in a ros workspace."""

    def __init__(self):
        """If your executor requires some initialization, use the class constructor for it"""
        logging.debug("[RosPackExecutor] init")

    def execute(self, args):
        """Method where the main behaviour of the executer should be"""
        logging.debug("[RosPackExecutor] execute. Args received: " + str(args))

        dependency_manager = DependencyManager()
        if os.getuid() != 0 and not args.simulate:
            logging.error(
                "This command requires sudo to be able to install the dependencies. If you just want to simulate, use --simulate"
            )
            sys.exit(1)

        workspace_packages = []
        for path, _, files in os.walk(os.getcwd()):
            for name in files:
                if name == "package.xml":
                    if not is_catkin_blacklisted(path):
                        package = CatkinPackage(os.path.join(path, name))
                        dependency_manager.register_package(package)
                        workspace_packages.append(package.get_name())

        for package in workspace_packages:
            dependency_manager.exclude_package(package)

        dependency_manager.check_colisions()
        dependency_manager.calculare_installs()
        install_list = dependency_manager.get_install_list()
        for install_elem in install_list:
            if "version" in install_elem:
                install_package(
                    install_elem["name"],
                    install_elem["version"],
                    simulate=args.simulate,
                )
            else:
                install_package(install_elem["name"], simulate=args.simulate)

    @staticmethod
    def add_expected_arguments(parser):
        """Method exposed for the handle to append our executer arguments."""
        parser.add_argument(
            "--simulate",
            action="store_true",
            help="Simulate the list of buildt dependencies that would be installed.",
            required=False,
        )
