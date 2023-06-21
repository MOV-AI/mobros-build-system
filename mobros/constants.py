"""Module to place all the package constants used throughout the package"""
from os import environ
from mobros import __version__
from enum import Enum
MOBROS_VERSION = __version__.version

environment = environ.get("ENV", "PROD")
MOVAI_SCRIPTS_BIN = "/usr/local/bin"

MOVAI_BASH_BUILD = MOVAI_SCRIPTS_BIN + "/ros1-workspace-build.sh"
MOVAI_BASH_PACK = MOVAI_SCRIPTS_BIN + "/ros1-workspace-package.sh"
MOVAI_BASH_RAISE = MOVAI_SCRIPTS_BIN + "/ros1-workspace-raise.sh"

MOVAI_GENERATED_ROSDEP_FILE = "/usr/local/rosdep/ros-pkgs.yaml"

if environment == "PROD":
    SQS_URL = (
        "https://sqs.eu-west-1.amazonaws.com/109213826902/RosdepPatcher-prod-my-queue"
    )
else:
    SQS_URL = (
        "https://sqs.eu-west-1.amazonaws.com/109213826902/RosdepPatcher-dev-my-queue"
    )

# for tests

TEST_RESOURCE_SHELL_SCRIPT = "test.bash"

SUPPORTED_BUILD_MODES = ["DEBUG", "RELEASE"]

CATKIN_BLACKLIST_FILES = ["AMENT_IGNORE", "CATKIN_IGNORE", "COLCON_IGNORE"]

OPERATION_TRANSLATION_TABLE = {
    "<": "version_lt",
    "<=": "version_lte",
    "=": "version_eq",
    ">=": "version_gte",
    ">": "version_gt",
    "": "any",
}
OPERATION_TRANSLATION_TABLE_REVERSE = {
    "version_lt": "<",
    "version_lte": "<=",
    "version_eq": "=",
    "version_gte": ">=",
    "version_gt": ">",
    "any": "any",
}

class Commands(Enum):
    INSTALL = "install"
    INSTALL_BUILD_DEPS = "install-build-dependencies"
    BUILD = "build"
    PACK = "pack"
    PUBLISH = "publish"
    RAISE = "raise"
    PING = "ping"