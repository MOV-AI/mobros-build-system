from MovaiRosBuildSystem.utils.utilitary import execute_bash_script
from MovaiRosBuildSystem.constants import MOVAI_BASH_PACK

class RosPackExecutor():

    def __init__(self):
        print("init")

    def execute(self, args):
        execute_bash_script(MOVAI_BASH_PACK)

    @staticmethod
    def add_expected_arguments(parser):
        parser.add_argument("--expected_pack_arg", help ="help needed")
