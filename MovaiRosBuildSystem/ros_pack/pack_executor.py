
class RosPackExecutor():

    def __init__(self):
        print("init")

    @staticmethod
    def add_expected_arguments(parser):
        parser.add_argument("--expected_pack_arg", help ="help needed")

    def execute(self, args):
        print("pack execute")

