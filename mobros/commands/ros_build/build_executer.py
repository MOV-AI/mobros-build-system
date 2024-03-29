"""Module responsible for building a ros workspace"""
from os import environ, getcwd

import mobros.utils.logger as logging
from mobros.constants import MOVAI_BASH_BUILD
from mobros.utils.utilitary import execute_bash_script


class RosBuildExecuter:
    """Executor responsible for installing the ros workspace requirements, and do a catkin build of the workspace."""

    def __init__(self):
        """If your executor requires some initialization, use the class constructor for it"""
        logging.debug("[RosBuildExecutor] init")

    def execute(self, args):
        """Method where the main behaviour of the executer should be"""
        logging.debug("[RosBuildExecutor] execute. Args received: " + str(args))
        process_env = environ.copy()
        process_env["BUILD_MODE"] = args.mode.upper()
        execute_bash_script(MOVAI_BASH_BUILD, process_env)

    @staticmethod
    def add_expected_arguments(parser):
        """Method exposed for the handle to append our executer arguments."""

        parser.add_argument("--workspace", help="Ros workspace to be built. By default its where you execute mobros.", default=getcwd())
        parser.add_argument(
            "--mode",
            help="Build mode. Either debug or release. Default is release",
            required=False,
            default="release",
            choices=["debug", "release"]
        )

        return parser.parse_known_args()

    @staticmethod
    def get_description():
        """Method exposed to allow the handler to describe the command in the call of help"""
        return "Command to execute a catkin build in the workspace."
