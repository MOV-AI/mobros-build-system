import os

class RosPackExecutor():

    def __init__(self):
        print("init")


    def execute(self, args):
        print("pack execute")
        print("im here "+str(os.getcwd()))

    @staticmethod
    def add_expected_arguments(parser):
        parser.add_argument("--expected_pack_arg", help ="help needed")
