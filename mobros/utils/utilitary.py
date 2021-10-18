"""Module to provide reusable/utilitary functions for other modules"""

from os.path import exists
from subprocess import PIPE, CalledProcessError, Popen


def __process_shell_lines(command, envs=None):
    """Function that on the execution of a commandline command, yelds on each output"""

    with Popen(command, stdout=PIPE, text=True, env=envs) as popen:

        # print stdout as it goes.
        for stdout_line in iter(popen.stdout.readline, ""):
            yield stdout_line

        popen.stdout.close()
        return_code = popen.wait()

        if return_code:
            raise CalledProcessError(return_code, command)


def execute_shell_command(command, process_env=None):
    """Function that executes a command line command and prints all output of it"""

    for line in __process_shell_lines(command, process_env):
        # override the end character from \n not to have in between \n in each print.
        print(line, end="")


def execute_bash_script(script_path, process_env=None):
    """Function that wraps the call of a bash script with 'bash -c'"""
    if exists(script_path):
        execute_shell_command(["bash", "-c", script_path], process_env)
    else:
        raise Exception("file not found. File: " + script_path)
