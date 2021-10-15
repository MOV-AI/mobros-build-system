"""Module to provide reusable/utilitary functions for other modules"""  # noqa: E501

from os.path import exists
from subprocess import PIPE, CalledProcessError, Popen


def __process_shell_lines(command):
    """Function that on the execution of a commandline command, yelds on each output"""  # noqa: E501

    with Popen(command, stdout=PIPE, text=True) as popen:

        # print stdout as it goes.
        for stdout_line in iter(popen.stdout.readline, ""):
            yield stdout_line

        popen.stdout.close()
        return_code = popen.wait()

        if return_code:
            raise CalledProcessError(return_code, command)


def execute_shell_command(command):
    """Function that executes a command line command and prints all output of it"""  # noqa: E501

    for line in __process_shell_lines(command):
        # override the end character from \n not to have in between \n in each print.  # noqa: E501
        print(line, end="")


def execute_bash_script(script_path):
    """Function that wraps the call of a bash script with 'bash -c'"""  # noqa: E501

    if exists(script_path):
        execute_shell_command(["bash", "-c", script_path])
    else:
        raise Exception("file not found. File: " + script_path)
