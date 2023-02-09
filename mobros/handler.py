"""Main package module. Contains the handler, executors and other modules inside."""
import argparse
import sys

import mobros.utils.logger as logging
from mobros.constants import SUPPORTED_BUILD_MODES
from mobros.ros_build.build_executor import RosBuildExecutor
from mobros.ros_install_build_deps.install_deps_executor import (
    InstallBuildDependsExecutor,
)
from mobros.ros_pack.pack_executor import RosPackExecutor
from mobros.ros_raise.raise_executor import RosRaiseExecutor
from mobros.ros_rosdep_publish.rosdep_pub_executor import RosdepPublishExecutor

executors = {
    "install-build-dependencies": InstallBuildDependsExecutor,
    "build": RosBuildExecutor,
    "pack": RosPackExecutor,
    "publish": RosdepPublishExecutor,
    "raise": RosRaiseExecutor,
}


def validate_build_mode(build_mode_input):
    """Method to guarantee only valid build modes pass to the commands."""

    if build_mode_input.upper() not in SUPPORTED_BUILD_MODES:
        logging.error(
            "Invalid build mode ("
            + build_mode_input
            + ")! please use one of the supported values"
            + str(SUPPORTED_BUILD_MODES).lower()
            + " !"
        )
        sys.exit(1)


def handle():
    """Entrypoint method of the package. It forwards commands to the executers"""

    parser = argparse.ArgumentParser(
        description="Framework to ease building, packaging and version raising of MOVAI ROS projects."
    )

    parser.add_argument("command", help="Command to be executed.")
    parser.add_argument("--workspace", help="Ros workspace.")
    parser.add_argument(
        "--mode",
        help="Build mode. Either debug or release. Default is release",
        required=False,
        default="release",
    )
    parser.add_argument(
        "--rosdep-install-dependency-types",
        help="Types of packages to be installed by rosdep. Default is 'all'",
        required=False,
        default="all",
    )

    # executor arguments
    for executer in executors.values():
        executer.add_expected_arguments(parser)

    args = parser.parse_args()
    logging.debug("Command received: " + args.command)

    validate_build_mode(args.mode)

    try:
        executor = executors[args.command]()
    except KeyError:
        logging.error(
            "Invalid command: "
            + args.command
            + ". Supported commands are: ("
            + " ".join(map(str, executors))
            + ")"
        )
        sys.exit()
    executor.execute(args)


if __name__ == "__main__":
    handle()
