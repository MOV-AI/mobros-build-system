from MovaiRosBuildSystem.utils.utilitary import execute_bash_script
from MovaiRosBuildSystem.constants import MOVAI_BASH_BUILD
from os.path import isfile


class RosBuildExecutor():

    def __init__(self):
        print("Init")

    def execute(self, args):
        workspace = args.workspace
        execute_bash_script(MOVAI_BASH_BUILD)


    @staticmethod
    def add_expected_arguments(parser):
        parser.add_argument("--other", help ="help needed")
