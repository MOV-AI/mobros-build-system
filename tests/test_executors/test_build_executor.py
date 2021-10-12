import unittest
import mock
from MovaiRosBuildSystem.ros_build.build_executor import RosBuildExecutor
from tests.mocks.mock_argparse import MockArgParser
import argparse


class TestBuildExecutor(unittest.TestCase):

    @mock.patch('argparse.ArgumentParser.parse_args',
            return_value=argparse.Namespace(command="build"))
    def test_build_execute(self, mock):
        print("hello")
        RosBuildExecutor().execute(MockArgParser())