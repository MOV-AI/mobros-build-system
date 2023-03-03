"""Module responsible for packaging all ros components in a workspace"""
import boto3

import mobros.utils.logger as logging
from mobros.constants import MOVAI_GENERATED_ROSDEP_FILE, SQS_URL
from mobros.utils.utilitary import read_yaml_from_file


def send_to_sqs(yaml_content):
    """Method to send messages to our rosdep service, through the sqs service."""
    # Create SQS client
    sqs = boto3.client("sqs")

    response = sqs.send_message(
        QueueUrl=SQS_URL,
        DelaySeconds=0,
        MessageAttributes={},
        MessageBody=(yaml_content),
    )

    print(response["MessageId"])


class RosdepPublishExecuter:
    """Executor responsible for producing ros/ros-movai packages in a ros workspace."""

    def __init__(self):
        """If your executor requires some initialization, use the class constructor for it"""
        logging.debug("[RosPackExecutor] init")

    #pylint: disable=W0613
    def execute(self, _args):
        """Method where the main behaviour of the executer should be"""
        yaml_content = read_yaml_from_file(MOVAI_GENERATED_ROSDEP_FILE, True)
        # Send message to SQS queue
        send_to_sqs(yaml_content)

    #pylint: disable=W0613
    @staticmethod
    def add_expected_arguments(parser):
        """Method exposed for the handle to append our executer arguments."""
        return
