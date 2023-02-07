"""Module to provide reusable/utilitary functions for other modules"""

from io import StringIO
import sys
from os.path import exists
from subprocess import PIPE, CalledProcessError, Popen, run
import mobros.utils.logger as logging
from ruamel.yaml import YAML


def __process_shell_lines(command, envs=None):
    """Function that on the execution of a commandline command, yelds on each output"""

    with Popen(command, stdout=PIPE, universal_newlines=True, env=envs) as popen:

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

def execute_shell_command_with_output(command, process_env=None, stop_on_error=False):
    result = run(command, stdout=PIPE, stderr=PIPE, env=process_env)
    if result.returncode:
        if stop_on_error:
            logging.error("Failed to execute command. Details: "+result.stdout.decode('utf-8'))
            sys.exit(1)
        return result.stderr.decode('utf-8')
    else:
        return result.stdout.decode('utf-8')

    
    
def execute_bash_script(script_path, process_env=None):
    """Function that wraps the call of a bash script with 'bash -c'"""
    if exists(script_path):
        execute_shell_command(["bash", "-c", script_path], process_env)
    else:
        raise Exception("file not found. File: " + script_path)


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
