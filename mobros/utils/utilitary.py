"""Module to provide reusable/utilitary functions for other modules"""

import sys
from io import StringIO
from os.path import exists
from subprocess import PIPE, CalledProcessError, Popen

from ruamel.yaml import YAML

import mobros.utils.logger as logging


def __process_shell_stdout_lines(command, envs=None, shell_mode=False):
    """Function that on the execution of a commandline command, yelds on each output"""
    
    with Popen(command, shell=shell_mode, stdout=PIPE, universal_newlines=True, env=envs) as popen:
        # print stdout as it goes.
        for stdout_line in iter(popen.stdout.readline, ""):
            yield stdout_line
        popen.stdout.close()
        return_code = popen.wait()

        if return_code:
            raise CalledProcessError(return_code, command)


def __process_shell_stderr_lines(command, envs=None, shell_mode=False):
    """Function that on the execution of a commandline command, yelds on each output"""
    
    with Popen(command, shell=shell_mode, stderr=PIPE, universal_newlines=True, env=envs) as popen:
        # print stdout as it goes.
        for stderr_line in iter(popen.stderr.readline, ""):
            yield stderr_line
        popen.stderr.close()
        popen.wait()


def execute_shell_command(command, log_output=False, process_env=None, stop_on_error=False, check_stderr=False, shell_mode=False):
    """Function that executes a command line command and prints all output of it"""

    logging.debug("[execute_shell_command - live] Command: " + str(command))
    
    output_lines = []
    try:

        if check_stderr:
            for line in __process_shell_stderr_lines(command, process_env, shell_mode=shell_mode):
                # override the end character from \n not to have in between \n in each print.
                clean_line = line.strip()
                if log_output:
                    logging.info(clean_line)
                output_lines.append(clean_line)
        else:
            
            for line in __process_shell_stdout_lines(command, process_env, shell_mode=shell_mode):
                # override the end character from \n not to have in between \n in each print.
                clean_line = line.strip()
                if log_output:
                    logging.info(clean_line)
                output_lines.append(clean_line)


        return output_lines
    except CalledProcessError:
        if stop_on_error:
            sys.exit(1)
        return output_lines


def execute_command(command, process_env=None):
    """Function that executes command with live output"""
    for line in __process_shell_stdout_lines(command, process_env):
        # override the end character from \n not to have in between \n in each print.
        print(line, end="")


def execute_bash_script(script_path, process_env=None, shell_mode=False):
    """Function that wraps the call of a bash script with 'bash -c'"""
    if exists(script_path):
        execute_shell_command(["bash", "-c", script_path], process_env=process_env, log_output=True, stop_on_error=True, shell_mode=shell_mode)
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

ROSDEP_RESULT_HEADER = "#apt"
ROSDEP_NEED_UPDATE_ANCHOR = "your rosdep installation has not been initialized yet"
ROSDEP_NOT_FOUND = "no rosdep rule for"


def detected_need_for_rosdep_update(cmd_output):
    """function that evaluates if the rosdep command is requesting rosdep update

    Args:
        cmd_output (str): rosdep command output

    Returns:
        needs_update: boolean that identifies if requires rosdep update first
    """
    return ROSDEP_NEED_UPDATE_ANCHOR in str(cmd_output)


def translate_package_name(rosdep_key):
    """Function that uses rosdep to translate a catkin package name to a debian package name

    Args:
        rosdep_key (str): catkin package name

    Returns:
        debian_pkg_name : debian package name
    """
    output_lines = execute_shell_command(["rosdep", "resolve", rosdep_key], stop_on_error=True, log_output=False)

    for line in output_lines:
        if ROSDEP_RESULT_HEADER not in line:
            translation = line.strip()
            logging.debug("[rosdep translate] Found translation for " + rosdep_key + ". It is " + translation)
    return translation

def write_to_file(path_to_file, content):
    """Function to write a json dict into a file"""

    with open(path_to_file, "w", encoding="utf8") as f:
        f.writelines(content)