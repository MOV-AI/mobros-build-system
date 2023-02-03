"""Module responsible for packaging all ros components in a workspace"""
import os

import mobros.utils.logger as logging
from mobros.constants import MOVAI_BASH_PACK
from mobros.utils.utilitary import execute_bash_script
from mobros.ros_install_build_deps.dependency_manager import DependencyManager
from mobros.ros_install_build_deps.catkin_package_manager import CatkinPackage, is_catkin_blacklisted


class InstallBuildDependsExecutor:
    """Executor responsible for producing ros/ros-movai packages in a ros workspace."""

    def __init__(self):
        """If your executor requires some initialization, use the class constructor for it"""
        logging.debug("[RosPackExecutor] init")

    def execute(self, args):
        """Method where the main behaviour of the executer should be"""
        logging.debug("[RosPackExecutor] execute. Args received: " + str(args))
        process_env = os.environ.copy()
        process_env["MOVAI_PACKAGING_DIR"] = args.workspace
        process_env["MOVAI_PACKAGE_RAISE_TYPE"] = "CI"
        process_env["BUILD_MODE"] = args.mode.upper()
        dependency_manager = DependencyManager()
        
        for path, subdirs, files in os.walk(os.getcwd()):
          for name in files:
            if name == "package.xml":

              if not is_catkin_blacklisted(path):
                package = CatkinPackage(os.path.join(path, name))
                dependency_manager.register_package(package)

        dependency_manager.check_colisions()
        dependency_manager.calculare_installs()
    @staticmethod
    def add_expected_arguments(parser):
        """Method exposed for the handle to append our executer arguments."""
        return
