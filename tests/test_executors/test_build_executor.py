import unittest
import mock
import argparse


class TestBuildExecutor(unittest.TestCase):

    @mock.patch('argparse.ArgumentParser.parse_args', return_value=argparse.Namespace(command="build"))  # noqa: E501
    def test_build_execute(self, mock):
        print("hello")
        # RosBuildExecutor().execute(MockArgParser())
