import unittest
import mock
from MovaiRosBuildSystem.handler import handle
import argparse

class TestHandler(unittest.TestCase):

    @mock.patch('argparse.ArgumentParser.parse_args',return_value=argparse.Namespace(command="build", workspace="dsa"))
    def test_build_command(self, mock):
        print("hello")
        handle()