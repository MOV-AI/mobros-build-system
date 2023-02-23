"""Module responsible for building a ros workspace"""
from os import environ

import mobros.utils.logger as logging
from mobros.constants import MOVAI_BASH_BUILD
from mobros.utils.utilitary import execute_bash_script


class RosBuildExecutor:
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
        parser.add_argument("--other", help="help needed")
