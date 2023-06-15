import argparse
import unittest

import mock

from mobros.handler import handle


def mock_add_expected_arguments(parser):
    return [None, None]

argparse_executor_build = argparse.Namespace(
    command="build", workspace="DUMMY_PATH", mode="debug", h=False
)
argparse_executor_pack = argparse.Namespace(
    command="pack", workspace="DUMMY_PATH", mode="debug", h=False
)


class TestHandler(unittest.TestCase):
    @mock.patch("mobros.commands.ros_pack.pack_executer.RosPackExecuter.execute")
    @mock.patch("mobros.commands.ros_build.build_executer.RosBuildExecuter.execute")
    @mock.patch(
        "argparse.ArgumentParser.parse_known_args", return_value=[argparse_executor_build,None]
    )
    def test_handler_build_forward(
        self, mock_argparse, mock_exec_build, mock_exec_pack
    ):
        handle()
        mock_exec_build.assert_called_with(argparse_executor_build)
        mock_exec_pack.assert_not_called()

    @mock.patch("mobros.commands.ros_pack.pack_executer.RosPackExecuter.execute")
    @mock.patch("mobros.commands.ros_build.build_executer.RosBuildExecuter.execute")
    @mock.patch(
        "argparse.ArgumentParser.parse_known_args", return_value=[argparse_executor_pack, None]
    )
    def test_handler_pack_forward(self, mock_argparse, mock_exec_build, mock_exec_pack):
        handle()
        mock_exec_build.assert_not_called()
        mock_exec_pack.assert_called_with(argparse_executor_pack)

    argeparse_extra_arg = argparse.Namespace(
        command="build", workspace="DUMMY_PATH", dummy_arg="test", mode="debug", h=False
    )
