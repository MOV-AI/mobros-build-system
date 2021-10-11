import unittest
import mock
from MovaiRosBuildSystem.handler import handle


class TestHandler(unittest.TestCase):

    def test_build_command(self):
        print("hello")
        handle()