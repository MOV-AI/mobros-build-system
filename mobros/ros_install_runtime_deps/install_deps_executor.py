"""Module responsible for packaging all ros components in a workspace"""
import os
import sys

import mobros.utils.logger as logging
from mobros.ros_install_runtime_deps.debian_package import (
    DebianPackage
)
from mobros.ros_install_build_deps.dependency_manager import DependencyManager
from mobros.utils.apt_utils import install_package, inspect_package

def is_version_mobros_pkg(version):
    print(version + " is  "+str(version.split("-")[1].isnumeric()))
    return version.split("-")[1].isnumeric()


def is_ros_package(name):
    return name.startswith("ros-")

class InstallRuntimeDependsExecutor:
    """Executor responsible for producing ros/ros-movai packages in a ros workspace."""

    def __init__(self):
        """If your executor requires some initialization, use the class constructor for it"""
        logging.debug("[RosInstallDepExecuter] init")

    def execute(self, args):
        """Method where the main behaviour of the executer should be"""
        logging.debug("[RosInstallDepExecuter] execute. Args received: " + str(args))

        dependency_manager = DependencyManager()
        # if os.getuid() != 0 and not args.simulate:
        #     logging.error(
        #         "This command requires sudo to be able to install the dependencies. If you just want to simulate, use --simulate"
        #     )
        #     sys.exit(1)
        
        install_pkgs = args.pkg_list
        dependency_manager = DependencyManager()
        for pkg_input_data in install_pkgs:
            version = ""
            name = pkg_input_data
            if "=" in pkg_input_data:
                name, version= pkg_input_data.split("=")
                print(name + " - "+version)

            package = DebianPackage(name, version, None)
            dependency_manager.register_package(package)
                
        first_tree_level=True
        packages_uninspected=[]
        known_packages=[]
        while(len(packages_uninspected) > 0 or first_tree_level ):
            print("looping list is ....")

            if first_tree_level:
                first_tree_level= False
                
            else:
                for package_to_inspect in packages_uninspected:
                    #if is_version_mobros_pkg(package_to_inspect["version"]):
                    if is_ros_package(package_to_inspect["name"]):
                        dependency_manager.register_package(DebianPackage(package_to_inspect["name"], package_to_inspect["version"], package_to_inspect["from"]))
    
            dependency_manager.check_colisions()
            dependency_manager.calculare_installs()
            install_list = dependency_manager.get_install_list()
            packages_uninspected=[]
            for candidate in install_list:

                if candidate["name"] not in known_packages:
                    known_packages.append(candidate["name"])
                    packages_uninspected.append(candidate)
                    
        
        print(install_list)
        
    @staticmethod
    def add_expected_arguments(parser):
        """Method exposed for the handle to append our executer arguments."""
        parser.add_argument('pkg_list', type=str, nargs='+')