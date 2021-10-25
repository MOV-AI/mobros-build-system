import argparse
import unittest

import mock

from mobros.handler import handle


def mock_add_expected_arguments(parser):
    parser.add_argument("--dummy_arg")


argeparse_executor_build = argparse.Namespace(command="build", workspace="DUMMY_PATH")
argeparse_executor_pack = argparse.Namespace(command="pack", workspace="DUMMY_PATH")


class TestHandler(unittest.TestCase):
    @mock.patch("mobros.ros_pack.pack_executor.RosPackExecutor.execute")
    @mock.patch("mobros.ros_build.build_executor.RosBuildExecutor.execute")
    @mock.patch(
        "argparse.ArgumentParser.parse_args", return_value=argeparse_executor_build
    )
    def test_handler_build_forward(
        self, mock_argparse, mock_exec_build, mock_exec_pack
    ):
        handle()
        mock_exec_build.assert_called_with(argeparse_executor_build)
        mock_exec_pack.assert_not_called()

    @mock.patch("mobros.ros_pack.pack_executor.RosPackExecutor.execute")
    @mock.patch("mobros.ros_build.build_executor.RosBuildExecutor.execute")
    @mock.patch(
        "argparse.ArgumentParser.parse_args", return_value=argeparse_executor_pack
    )
    def test_handler_pack_forward(self, mock_argparse, mock_exec_build, mock_exec_pack):
        handle()
        mock_exec_build.assert_not_called()
        mock_exec_pack.assert_called_with(argeparse_executor_pack)

    argeparse_extra_arg = argparse.Namespace(
        command="build", workspace="DUMMY_PATH", dummy_arg="test"
    )

    @mock.patch(
        "mobros.ros_pack.pack_executor.RosPackExecutor.add_expected_arguments",
        side_effect=mock_add_expected_arguments,
    )
    @mock.patch("mobros.ros_build.build_executor.RosBuildExecutor.execute")
    @mock.patch("argparse.ArgumentParser.parse_args", return_value=argeparse_extra_arg)
    def test_handler_request_executor_arguments(
        self, mock_argparse, mock_exec_build, mock_add_arg
    ):
        handle()

        mock_add_arg.assert_called_once()

        expected_value = self.argeparse_extra_arg.dummy_arg
        obtained_value = mock_exec_build.call_args.args[0].dummy_arg

        self.assertEqual(expected_value, obtained_value)
