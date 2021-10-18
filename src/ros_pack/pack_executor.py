"""Module responsible for packaging all ros components in a workspace"""
from os import environ

import src.utils.logger as logging
from src.constants import MOVAI_BASH_PACK
from src.utils.utilitary import execute_bash_script


class RosPackExecutor:
    """Executor responsible for producing ros/ros-movai packages in a ros workspace."""

    def __init__(self):
        """If your executor requires some initialization, use the class constructor for it"""
        logging.debug("[RosPackExecutor] init")

    def execute(self, args):
        """Method where the main behaviour of the executer should be"""
        logging.debug("[RosPackExecutor] execute. Args received: " + str(args))
        process_env = environ.copy()
        process_env["MOVAI_PACKAGING_DIR"] = args.workspace

        execute_bash_script(MOVAI_BASH_PACK, process_env)

    @staticmethod
    def add_expected_arguments(parser):
        """Method exposed for the handle to append our executer arguments."""
        parser.add_argument("--expected_pack_arg", help="help needed")
