"""Main package module. Contains the handler, executors and other modules inside."""
import argparse
import sys

import mobros.utils.logger as logging
from mobros.ros_build.build_executor import RosBuildExecutor
from mobros.ros_pack.pack_executor import RosPackExecutor

executors = {"build": RosBuildExecutor, "pack": RosPackExecutor}


def handle():
    """Entrypoint method of the package. It handles commands to the executers"""

    parser = argparse.ArgumentParser(
        description="Framework to ease building, packaging and version raising of MOVAI ROS projects."
    )

    parser.add_argument("command", help="Command to be executed.")
    parser.add_argument("--workspace", help="Ros workspace.")

    # executor arguments
    for executer in executors.values():
        executer.add_expected_arguments(parser)

    args = parser.parse_args()
    logging.debug("Command received: " + args.command)

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
