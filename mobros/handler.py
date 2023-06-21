"""Main package module. Contains the handler, executors and other modules inside."""
import argparse
import sys

import mobros.utils.logger as logging
from mobros.commands.ping.ping_executer import PingExecuter
from mobros.commands.ros_build.build_executer import RosBuildExecuter
from mobros.commands.ros_install_build_deps.install_deps_executer import (
    InstallBuildDependsExecuter,
)
from mobros.commands.ros_install_runtime_deps.install_deps_executer import (
    InstallRuntimeDependsExecuter,
)
from mobros.commands.ros_pack.pack_executer import RosPackExecuter
from mobros.commands.ros_raise.raise_executer import RosRaiseExecuter
from mobros.commands.ros_rosdep_publish.rosdep_pub_executer import RosdepPublishExecuter
from mobros.constants import MOBROS_VERSION, Commands

executors = {
    Commands.INSTALL_BUILD_DEPS.value: InstallBuildDependsExecuter,
    Commands.BUILD.value: RosBuildExecuter,
    Commands.PACK.value: RosPackExecuter,
    Commands.INSTALL.value: InstallRuntimeDependsExecuter,
    Commands.PUBLISH.value: RosdepPublishExecuter,
    Commands.RAISE.value: RosRaiseExecuter,
    Commands.PING.value: PingExecuter,
}

def handle():
    """Entrypoint method of the package. It forwards commands to the executers"""

    pre_parser = argparse.ArgumentParser(
        description="Framework to ease building, packaging, installing and version raising of ROS projects.",
        add_help=False
    )
    pre_parser.add_argument("command", help="Command to be executed. Supported commands are: ("
            + " ".join(map(str, executors))
            + ")", choices=executors.keys())

    pre_parser.add_argument('--help','--h', action="store_true", dest="h",help='help for help if you need some help')

    # executor arguments
    # pylint: disable=W0718
    try:
        ns, _ = pre_parser.parse_known_args()
    except Exception:
        pre_parser.print_help()
        sys.exit(0)

    command = ns.command

    if command != Commands.PING.value:
        logging.userInfo("Mobros version: "+MOBROS_VERSION)

    h = ns.h

    sub = pre_parser.add_subparsers()
    try:
        executer = executors[command]
        sub_parser = sub.add_parser(command, description=executer.get_description())

        args, _ = executer.add_expected_arguments(sub_parser)
        if h:
            sub_parser.print_help()
            sys.exit(0)

        executer = executors[command]()

    except KeyError:
        logging.error(
            "Invalid command: "
            + command
            + ". Supported commands are: ("
            + " ".join(map(str, executors))
            + ")"
        )
        sys.exit()

    if isinstance(args,tuple):
        args=args[0]

    executer.execute(args)

if __name__ == "__main__":
    handle()
