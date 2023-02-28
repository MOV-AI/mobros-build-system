import argparse
import unittest

import mock


class TestBuildExecuter(unittest.TestCase):
    @mock.patch(
        "argparse.ArgumentParser.parse_args",
        return_value=argparse.Namespace(command="build"),
    )
    def test_build_execute(self, mock):
        print("hello")
        # RosBuildExecutor().execute(MockArgParser())
