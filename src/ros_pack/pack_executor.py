"""Module responsible for packaging all ros components in a workspace"""  # noqa: E501
from src.constants import MOVAI_BASH_PACK
from src.utils.utilitary import execute_bash_script


class RosPackExecutor:
    """Executor responsible for producing ros/ros-movai packages in a ros workspace."""  # noqa: E501

    def __init__(self):
        """If your executor requires some initialization, use the class constructor for it"""  # noqa: E501
        print("init")

    def execute(self, args):
        """Method where the main behaviour of the executer should be"""
        execute_bash_script(MOVAI_BASH_PACK)

    @staticmethod
    def add_expected_arguments(parser):
        """Method exposed for the handle to append our executer arguments."""
        parser.add_argument("--expected_pack_arg", help="help needed")
