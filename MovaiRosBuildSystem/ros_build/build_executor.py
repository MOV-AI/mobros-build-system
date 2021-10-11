

class RosBuildExecutor():

    def __init__(self):
        print("Init")

    @staticmethod
    def add_expected_arguments(parser):
        parser.add_argument("--other", help ="help needed")

    def execute(self, args):
        print("build execute")

