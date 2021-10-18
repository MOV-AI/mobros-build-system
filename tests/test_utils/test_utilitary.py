import unittest
import mock
from src.utils.utilitary import execute_shell_command, execute_bash_script
from src.constants import TEST_RESOURCE_SHELL_SCRIPT
from os.path import dirname, realpath, exists
from os import remove

dir_path = dirname(realpath(__file__))
relative_path_to_resources = dir_path + "/../resources/"
SHELL_SCRIPT_PATH = relative_path_to_resources + TEST_RESOURCE_SHELL_SCRIPT

SHELL_SCRIPT_OUTPUT_FILE = "/tmp/trash-test.txt"


class TestUtilitary(unittest.TestCase):

    def setUp(self):
        if (exists(SHELL_SCRIPT_OUTPUT_FILE)):
            remove(SHELL_SCRIPT_OUTPUT_FILE)

    def tearDown(self):
        if (exists(SHELL_SCRIPT_OUTPUT_FILE)):
            remove(SHELL_SCRIPT_OUTPUT_FILE)

    def test_execute_shell_command_behaviour(self):

        sh_cmd = ['bash', '-c', SHELL_SCRIPT_PATH]
        execute_shell_command(sh_cmd)

        self.assertTrue(exists(SHELL_SCRIPT_OUTPUT_FILE))

    @mock.patch('builtins.print')
    def test_execute_shell_command_output(self, mock_print):

        sh_cmd = ['bash', '-c', SHELL_SCRIPT_PATH]
        execute_shell_command(sh_cmd)

        cat_cmd = ['cat', SHELL_SCRIPT_OUTPUT_FILE]
        execute_shell_command(cat_cmd)

        mock_print.assert_called_with('test\n', end='')

    def test_execute_bash_fail_file_not_found(self):
        try:
            execute_bash_script("/tmp/non-existent-file.sh")
            self.assertTrue(False)
        except Exception:
            pass
