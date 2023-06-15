"""Module to check if the mobros is present"""
import mobros.utils.logger as logging


class PingExecuter:
    """Executor responsible for installing the ros workspace requirements, and do a catkin build of the workspace."""

    def __init__(self):
        """init"""

    # pylint: disable=W0613
    def execute(self, args):
        """Method where the main behaviour of the executer should be"""
        logging.info("pong")

    # pylint: disable=W0613
    @staticmethod
    def add_expected_arguments(parser):
        """Method exposed for the handle to append our executer arguments."""
        return parser.parse_known_args()

    @staticmethod
    def get_description():
        """Method exposed to allow the handler to describe the command in the call of help"""
        return "Simple command to check if mobros is healthy. It should respond with 'ping'"
