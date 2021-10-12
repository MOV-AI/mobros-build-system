from subprocess import Popen, PIPE, CalledProcessError
from os.path import exists

def __process_shell_lines(command):
    popen = Popen(command, stdout=PIPE, universal_newlines=True)

    # print stdout as it goes.
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line 

    popen.stdout.close()
    return_code = popen.wait()

    if return_code:
        raise CalledProcessError(return_code, command)


def execute_shell_command(command):
    for line in __process_shell_lines(command):
        #override the end character from \n not to have in between \n in each print.
        print(line, end="")

def execute_bash_script(script_path):
    if (exists(script_path)):
        execute_shell_command(['bash', '-c', script_path])
    else:
        raise Exception("file not found. File: "+script_path)