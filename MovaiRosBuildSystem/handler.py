from MovaiRosBuildSystem.ros_build.build_executor import RosBuildExecutor
from MovaiRosBuildSystem.ros_pack.pack_executor import RosPackExecutor
import argparse

executors = {
    "build":RosBuildExecutor,
    "pack":RosPackExecutor
 }

def handle():
    parser = argparse.ArgumentParser(
            description="Framework to ease build, pack and raise of ros movai projects."
        )

    parser.add_argument('command', help='Command to be executed.')

    # executor arguments
    for executor in executors:
        executors[executor].add_expected_arguments(parser)

    args = parser.parse_args()

    builder = executors[args.command]()
    builder.execute(args)




if (__name__ == '__main__'):
    handle()