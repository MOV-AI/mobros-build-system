from MovaiRosBuildSystem.utils.utilitary import execute_shell_command
from MovaiRosBuildSystem.constants import MOVAI_BASH_PACKAGING, MOVAI_BASH_BUILD
from os.path import isfile


def install_project_requirements(workspace):
    
    if (isfile( MOVAI_BASH_BUILD)):
        print("Found ros1-workspace-build.sh")

        shell_catkin_build_cmd=['bash' , '-c', MOVAI_BASH_BUILD]
        execute_shell_command(shell_catkin_build_cmd)
    else:
        print("nope")
    


class RosBuildExecutor():

    def __init__(self):
        print("Init")



    def execute(self, args):
        workspace = args.workspace
        install_project_requirements(workspace)



    @staticmethod
    def add_expected_arguments(parser):
        parser.add_argument("--other", help ="help needed")
