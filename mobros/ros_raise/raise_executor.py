"""Module responsible for raising the version on a ros workspace. Finds and raises the main package of it. Then propagates the version to others."""
from os import environ

import mobros.utils.logger as logging
from mobros.constants import MOVAI_BASH_RAISE
from mobros.utils.utilitary import execute_bash_script


class RosRaiseExecutor:
    """Executor responsible for finding and raising the main ros package in a workspace"""

    def __init__(self):
        """If your executor requires some initialization, use the class constructor for it"""
        logging.debug("[RosRaiseExecutor] init")

    def execute(self, args):
        """Method where the main behaviour of the executer should be"""
        logging.debug("[RosRaiseExecutor] execute. Args received: " + str(args))
        process_env = environ.copy()
        process_env["MOVAI_PACKAGING_DIR"] = args.workspace
        process_env["MOVAI_PACKAGE_RAISE_TYPE"] = "CI"

        execute_bash_script(MOVAI_BASH_RAISE, process_env=process_env)

    @staticmethod
    def add_expected_arguments(parser):
        """Method exposed for the handle to append our executer arguments."""
        parser.add_argument("--dummy_raise_arg", help="help needed")
