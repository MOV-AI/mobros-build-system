"""Module responsible for packaging all ros components in a workspace"""
import os
import sys

import mobros.utils.logger as logging
from mobros.ros_install_build_deps.catkin_package import (
    CatkinPackage,
    is_catkin_blacklisted,
)
from mobros.ros_install_build_deps.dependency_manager import DependencyManager
from mobros.utils.apt_utils import install_package
from mobros.utils import utilitary

class InstallBuildDependsExecutor:
    """Executor responsible for producing ros/ros-movai packages in a ros workspace."""

    def __init__(self):
        """If your executor requires some initialization, use the class constructor for it"""
        logging.debug("[RosInstallBuildDepExecutor] init")

    def execute(self, args):
        """Method where the main behaviour of the executer should be"""
        logging.debug("[RosInstallBuildDepExecutor] execute. Args received: " + str(args))

        dependency_manager = DependencyManager()
        if os.getuid() != 0 and not args.simulate:
            logging.error(
                "This command requires sudo to be able to install the dependencies. If you just want to simulate, use --simulate"
            )
            sys.exit(1)
        
        utilitary.execute_shell_command(["rosdep", "update"], stop_on_error=True, log_output=True)
        
        workspace_packages = []
        for path, _, files in os.walk(os.getcwd()):
            for name in files:
                if name == "package.xml":
                    if not is_catkin_blacklisted(path):
                        package = CatkinPackage(os.path.join(path, name))
                        dependency_manager.register_package(package)
                        workspace_packages.append(package.get_name())

        # exclude the package present in the workspace from the build dependency list to be installed. They are built.
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
