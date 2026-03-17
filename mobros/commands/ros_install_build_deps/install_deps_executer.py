"""Module responsible for packaging all ros components in a workspace"""
import argparse
import os
import sys
from os import getcwd
import mobros.utils.logger as logging
from mobros.commands.ros_install_build_deps.catkin_package import (
    CatkinPackage,
    is_catkin_blacklisted,
)
from mobros.commands.ros_install_runtime_deps.install_deps_executer import (
    InstallRuntimeDependsExecuter,
)
from mobros.dependency_manager.dependency_manager import DependencyManager
from mobros.utils import apt_utils


class InstallBuildDependsExecuter:
    """Executor responsible for producing ros/ros-movai packages in a ros workspace."""

    def __init__(self):
        """If your executor requires some initialization, use the class constructor for it"""
        logging.debug("[RosInstallBuildDepExecutor] init")

    # pylint: disable=R0915
    def execute(self, args):
        """Method where the main behaviour of the executer should be"""
        logging.debug(
            "[RosInstallBuildDepExecutor] execute. Args received: " + str(args)
        )

        dependency_manager = DependencyManager()
        if os.getuid() != 0 and not args.simulate:
            logging.error(
                "This command requires sudo to be able to install the dependencies. If you just want to simulate, use --simulate"
            )
            sys.exit(1)

        apt_utils.execute_shell_command(
            [
                "rosdep",
                "update",
                "--include-eol-distros",
                "--rosdistro=" + os.getenv("ROS_DISTRO", "noetic"),
            ],
            stop_on_error=True,
            log_output=True,
        )
        workspace = args.workspace
        workspace_packages_paths = {}
        packages_dependencies= {}
        for path, _, files in os.walk(workspace):
            for name in files:
                if name == "package.xml":
                    if not is_catkin_blacklisted(path):

                        #dependency_manager.register_package(package)
                        package_path = os.path.join(path, name)
                        workspace_packages_paths[CatkinPackage.extract_name(package_path)] = package_path

        for _, package_path in workspace_packages_paths.items():
            package = CatkinPackage(package_path, workspace_packages_paths.keys())
            dependency_manager.register_package(package)
            # Store all dependencies in a dict of sets, where the key is the dependency name and the value is a set of frozensets with the rules.
            for dependency_name,rules in package.get_dependencies().items():
                if dependency_name not in packages_dependencies:
                    packages_dependencies[dependency_name]=set()
                for rule in rules:
                    packages_dependencies[dependency_name].add(frozenset(rule.items()))

        dependency_manager.check_colisions()
        dependency_manager.calculate_installs()
        install_list = dependency_manager.get_install_list()

        pkgs_to_install = []
        for pkg in install_list:
            if "version" in pkg:
                # check if the dependency has any rules that are not "any". 
                # If they are all "any", we let the runtime install calculate it and not confuse it with "user" input priorities.
                rules_fs_set = packages_dependencies.get(pkg["name"], set())
                has_rules_besides_any = any(
                    dict(rule_fs).get("operator", "") != ""
                    for rule_fs in rules_fs_set
                )

                if has_rules_besides_any:
                    pkgs_to_install.append(pkg["name"] + "=" + pkg["version"])
                else:
                    logging.debug("Package "+str(pkg['name']) + " is a package dependency with any. Not passing version to apt.")
                    pkgs_to_install.append(pkg["name"])

            else:
                pkgs_to_install.append(pkg["name"])

        if len(pkgs_to_install) == 0:
            logging.userInfo("No build dependencies detected!. Nothing todo.")
            sys.exit(0)

        argparse_args = argparse.Namespace(
            y=True, pkg_list=pkgs_to_install, upgrade_installed=True
        )

        executer = InstallRuntimeDependsExecuter()
        executer.execute(argparse_args)

        # for install_elem in install_list:
        #     if "version" in install_elem:
        #         install_package(
        #             install_elem["name"],
        #             install_elem["version"],
        #             simulate=args.simulate,
        #         )
        #     else:
        #         install_package(install_elem["name"], simulate=args.simulate)

    @staticmethod
    def add_expected_arguments(parser):
        """Method exposed for the handle to append our executer arguments."""
        parser.add_argument(
            "--simulate",
            action="store_true",
            help="Simulate the list of buildt dependencies that would be installed.",
            required=False,
        )
        parser.add_argument("--workspace", help="Ros workspace to scan the build dependencies from from. By default its where you execute mobros.", required=False, default=getcwd())
        return parser.parse_known_args()

    @staticmethod
    def get_description():
        """Method exposed to allow the handler to describe the command in the call of help"""
        return "Command responsible for installing the build dependencies needed in the specified workspace."
