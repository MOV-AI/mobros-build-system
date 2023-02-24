"""Module responsible for packaging all ros components in a workspace"""
import os
import sys
import time
import mobros.utils.logger as logging
from mobros.commands.ros_install_runtime_deps.debian_package import (
    DebianPackage
)
from mobros.dependency_manager.dependency_manager import DependencyManager
from mobros.utils.apt_utils import execute_shell_command,is_virtual_package, is_package_already_installed, get_package_installed_version
from anytree import LevelOrderGroupIter
import queue
from mobros.utils.utilitary import write_to_file

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

            if not is_virtual_package(name):

                package = DebianPackage(name, version, None)
                dependency_manager.register_root_package(name,version,"user")
                
                dependency_manager.register_package(package)
            else:
                logging.warning("Package: "+name + " is a virtual package. Skipping")
        
        first_tree_level=True
        packages_uninspected=[]
        known_packages=[]

        while(len(packages_uninspected) > 0 or first_tree_level ):

            if first_tree_level:
                first_tree_level= False
                
            else:

                for package_to_inspect in packages_uninspected:
                    #if is_version_mobros_pkg(package_to_inspect["version"]):
                    if not is_virtual_package(package_to_inspect["name"]):
                        package=DebianPackage(package_to_inspect["name"], package_to_inspect["version"], package_to_inspect["from"])

                        if not dependency_manager.is_user_requested_package(package_to_inspect["name"]):
                            installed_package_version=get_package_installed_version(name)
                            if installed_package_version:
                                if not args.upgrade_installed:
                                    dependency_manager.register_root_package(name, installed_package_version, "Installed")

                        dependency_manager.register_package(package)
                        
                    else:
                        logging.debug("Package: "+package_to_inspect["name"] + " is a virtual package. Skipping")
                
            dependency_manager.check_colisions()
            dependency_manager.calculate_installs()
            install_list = dependency_manager.get_install_list()
            packages_uninspected=[]
            for candidate in install_list:

                if candidate["name"] not in known_packages:
                    known_packages.append(candidate["name"])
                    packages_uninspected.append(candidate)

        
        dependency_manager.render_tree()

        install_queue= queue.LifoQueue()
        known_packages={}
        for tree_level in LevelOrderGroupIter(dependency_manager.root):
            for elem in tree_level:
                if elem.name not in known_packages:
                    install_queue.put(elem.name)
                    known_packages[elem.name]=None
        
        start1 = time.time()
        package_list=""
        while not install_queue.empty():
            deb_name = install_queue.get()
            if deb_name == "/":
                continue

            version = dependency_manager.get_version_of_candidate(deb_name)
            if not is_package_already_installed(deb_name, version):
                is_installed=is_package_already_installed(deb_name)
                if args.upgrade_installed or not is_installed:

                    if is_installed:
                        logging.warning("Installing "+deb_name+"="+version +" (Upgrading)")
                    else:
                        logging.important("Installing "+deb_name+"="+version)
    #                install_package(deb_name, version, simulate=args.simulate)
                    package_list += (
                        deb_name+"="+version
                        + "\n"
                    )

        if not args.y:
            val = input("You want to continue? (y/n): ")
            if val.lower() not in ["y","yes"]:
                logging.warning("Aborting.")
                sys.exit(1)

        write_to_file("packages.apt",package_list)

        execute_shell_command(
            "/usr/bin/apt install $(cat packages.apt) -y --allow-downgrades",
            stop_on_error=True,
            log_output=True,
            shell_mode=True
        )
        end1 = time.time()
        
        logging.debug("Installation took: "+str(end1 - start1))
        logging.important("Mobros install Successfull!")

        
    @staticmethod
    def add_expected_arguments(parser):
        """Method exposed for the handle to append our executer arguments."""
        parser.add_argument("--pkg_list",required=False, type=str, nargs='+',default=[],)
        parser.add_argument("--upgrade-installed", required=False, action="store_true",  dest="upgrade_installed")
