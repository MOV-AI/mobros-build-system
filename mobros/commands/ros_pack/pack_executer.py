"""Module responsible for packaging all ros components in a workspace"""
from os import environ

import mobros.utils.logger as logging
from mobros.constants import MOVAI_BASH_PACK
from mobros.utils.utilitary import execute_bash_script


class RosPackExecuter:
    """Executor responsible for producing ros/ros-movai packages in a ros workspace."""

    def __init__(self):
        """If your executor requires some initialization, use the class constructor for it"""
        logging.debug("[RosPackExecutor] init")

    def execute(self, args):
        """Method where the main behaviour of the executer should be"""
        logging.debug("[RosPackExecutor] execute. Args received: " + str(args))
        process_env = environ.copy()
        process_env["MOVAI_PACKAGING_DIR"] = args.workspace
        process_env["MOVAI_PACKAGE_RAISE_TYPE"] = "CI"
        process_env["BUILD_MODE"] = args.mode.upper()
        execute_bash_script(MOVAI_BASH_PACK, process_env)

    # pylint: disable=W0613
    @staticmethod
    def add_expected_arguments(parser):
        """Method exposed for the handle to append our executer arguments."""
        return
