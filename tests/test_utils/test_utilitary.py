import unittest
from os import remove
from os.path import dirname, exists, realpath

import mock

from mobros.constants import TEST_RESOURCE_SHELL_SCRIPT
from mobros.utils.utilitary import execute_bash_script, execute_shell_command

dir_path = dirname(realpath(__file__))
relative_path_to_resources = dir_path + "/../resources/"
SHELL_SCRIPT_PATH = relative_path_to_resources + TEST_RESOURCE_SHELL_SCRIPT

SHELL_SCRIPT_OUTPUT_FILE = "/tmp/trash-test.txt"


class TestUtilitary(unittest.TestCase):
    def setUp(self):
        if exists(SHELL_SCRIPT_OUTPUT_FILE):
            remove(SHELL_SCRIPT_OUTPUT_FILE)

    def tearDown(self):
        if exists(SHELL_SCRIPT_OUTPUT_FILE):
            remove(SHELL_SCRIPT_OUTPUT_FILE)

    def test_execute_shell_command_behaviour(self):
        sh_cmd = ["bash", "-c", SHELL_SCRIPT_PATH]
        execute_shell_command(sh_cmd)

        self.assertTrue(exists(SHELL_SCRIPT_OUTPUT_FILE))

    @mock.patch("mobros.utils.logger.info")
    def test_execute_shell_command_output(self, mock_print):
        sh_cmd = ["bash", "-c", SHELL_SCRIPT_PATH]
        execute_shell_command(sh_cmd, log_output=True)

        cat_cmd = ["cat", SHELL_SCRIPT_OUTPUT_FILE]
        execute_shell_command(cat_cmd, log_output=True)

        mock_print.assert_called_with("test")

    def test_execute_bash_fail_file_not_found(self):
        try:
            execute_bash_script("/tmp/non-existent-file.sh")
            self.assertTrue(False)
        except Exception:
            pass
