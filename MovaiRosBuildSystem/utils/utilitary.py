from subprocess import Popen, PIPE, CalledProcessError

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
        print(line, end="")