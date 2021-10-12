from os.path import isfile
from MovaiRosBuildSystem.constants import MOVAI_BASH_PACKAGING, MOVAI_BASH_BUILD
from MovaiRosBuildSystem.utils.utilitary import execute_shell_command, print_only

def install_project_requirements(workspace):
    
    if (isfile( MOVAI_BASH_PACKAGING)):
        print("exists")
        source_install_req_cmd=['bash' , '-c', MOVAI_BASH_BUILD]

        execute_shell_command(source_install_req_cmd)
        print_only(source_install_req_cmd)
        print(str("ola"))
        #exec_import_script_cmd=['sh' ,'-c', 'movai_install_rosinstall']
        #exit_code = call(exec_import_script_cmd)
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