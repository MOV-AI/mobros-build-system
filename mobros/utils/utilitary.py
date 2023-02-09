"""Module to provide reusable/utilitary functions for other modules"""

import sys
from io import StringIO
from os.path import exists
from subprocess import PIPE, CalledProcessError, Popen, run

from ruamel.yaml import YAML

import mobros.utils.logger as logging


def __process_shell_stdout_lines(command, envs=None):
    """Function that on the execution of a commandline command, yelds on each output"""

    with Popen(command, stdout=PIPE, universal_newlines=True, env=envs) as popen:
        # print stdout as it goes.
        for stdout_line in iter(popen.stdout.readline, ""):
            yield stdout_line
        popen.stdout.close()
        return_code = popen.wait()

        if return_code:
            raise CalledProcessError(return_code, command)

def __process_shell_stderr_lines(command, envs=None):
    """Function that on the execution of a commandline command, yelds on each output"""

    with Popen(command, stderr=PIPE, universal_newlines=True, env=envs) as popen:
        # print stdout as it goes.
        for stderr_line in iter(popen.stderr.readline, ""):
            yield stderr_line
        popen.stderr.close()
        return_code = popen.wait()

def execute_shell_command(command, log_output=False, process_env=None, stop_on_error=False, check_stderr=False):
    """Function that executes a command line command and prints all output of it"""

    logging.debug("[execute_shell_command - live] Command: " + str(command))
    try:
        output_lines = []
        if check_stderr:
            for line in __process_shell_stderr_lines(command, process_env):
                # override the end character from \n not to have in between \n in each print.
                if log_output:
                    logging.info(line, end="")
                output_lines.append(line)
        else:
            for line in __process_shell_stdout_lines(command, process_env):
                # override the end character from \n not to have in between \n in each print.
                if log_output:
                    logging.info(line, end="")
                output_lines.append(line)
            
        return output_lines
    except CalledProcessError:
        if stop_on_error:
            sys.exit(1)

def execute_command(command, process_env=None, stop_on_error=False):
    """Function that executes command with live output"""
    for line in __process_shell_stdout_lines(command, process_env):
        # override the end character from \n not to have in between \n in each print.
        print(line, end="")

def execute_bash_script(script_path, process_env=None):
    """Function that wraps the call of a bash script with 'bash -c'"""
    if exists(script_path):
        execute_shell_command(["bash", "-c", script_path], process_env)
    else:
        logging.error("file not found. File: " + script_path)


def read_yaml_from_file(path, as_string=False):
    """Method that from a file path, reads the content of the file, and interprets it as a yaml dict or simply string"""
    yaml = YAML()
    string_stream = StringIO()
    with open(path, encoding="utf-8") as f_handler:
        yaml_content = yaml.load(f_handler)

    if as_string:
        yaml.dump(yaml_content, string_stream)
        yaml_content = string_stream.getvalue()

    string_stream.close()
    return yaml_content
