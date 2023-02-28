import argparse
import unittest
import os
import mock
from mobros.commands.ros_install_build_deps.install_deps_executer import (
    InstallBuildDependsExecuter,
)
from tests.test_executers.mocks.mock_package import MockPackage
from mobros.utils.utilitary import read_from_file
import queue

DUMMY_AVAIABLE_VERSIONS = [
    "2.0.0-8",
    "2.0.0-7",
    "2.0.0-6",
    "2.0.0-5",
    "2.0.0-4",
    "2.0.0-3",
    "1.2.0-3",
    "1.2.0-2",
    "1.2.0-1",
    "1.1.0-3",
    "1.1.0-2",
    "1.1.0-1",
    "1.0.2-21",
    "1.0.2-20",
    "1.0.2-19",
    "1.0.2-18",
    "1.0.2-17",
    "1.0.2-16",
    "1.0.2-15",
    "1.0.2-14",
    "1.0.2-13",
    "1.0.2-12",
    "1.0.2-11",
    "1.0.2-10",
    "1.0.2-9",
    "1.0.2-8",
    "1.0.2-7",
    "1.0.2-6",
    "1.0.2-5",
    "1.0.2-4",
    "1.0.2-3",
    "1.0.2-2",
    "1.0.2-1",
    "1.0.1-4",
    "1.0.1-3",
    "1.0.1-2",
    "1.0.1-1",
    "1.0.0-100",
    "1.0.0-99",
    "1.0.0-98",
    "1.0.0-97",
    "1.0.0-96",
    "1.0.0-95",
    "1.0.0-94",
    "1.0.0-93",
    "1.0.0-92",
    "1.0.0-91",
    "1.0.0-90",
    "1.0.0-89",
    "1.0.0-88",
    "1.0.0-87",
    "1.0.0-86",
    "1.0.0-85",
    "1.0.0-84",
    "1.0.0-83",
    "1.0.0-82",
    "1.0.0-81",
    "1.0.0-80",
    "1.0.0-79",
    "1.0.0-78",
    "1.0.0-77",
    "1.0.0-76",
    "1.0.0-75",
    "1.0.0-74",
    "1.0.0-73",
    "1.0.0-72",
    "1.0.0-71",
    "1.0.0-70",
    "1.0.0-69",
    "1.0.0-68",
    "1.0.0-67",
    "1.0.0-66",
    "1.0.0-65",
    "1.0.0-64",
    "1.0.0-63",
    "1.0.0-62",
    "1.0.0-61",
    "1.0.0-60",
    "1.0.0-59",
    "1.0.0-58",
    "1.0.0-57",
    "1.0.0-56",
    "1.0.0-55",
    "1.0.0-54",
    "1.0.0-53",
    "1.0.0-52",
    "1.0.0-51",
    "1.0.0-50",
    "1.0.0-49",
    "1.0.0-48",
    "1.0.0-47",
    "1.0.0-46",
    "1.0.0-45",
    "1.0.0-44",
    "1.0.0-43",
    "1.0.0-42",
    "1.0.0-41",
    "1.0.0-40",
    "1.0.0-39",
    "1.0.0-38",
    "1.0.0-37",
    "1.0.0-36",
    "1.0.0-35",
    "1.0.0-34",
    "1.0.0-33",
    "1.0.0-32",
    "1.0.0-31",
    "1.0.0-30",
    "1.0.0-29",
    "1.0.0-28",
    "1.0.0-27",
    "1.0.0-26",
    "1.0.0-25",
    "1.0.0-24",
    "1.0.0-23",
    "1.0.0-22",
    "1.0.0-21",
    "1.0.0-20",
    "1.0.0-19",
    "1.0.0-18",
    "1.0.0-17",
    "1.0.0-16",
    "1.0.0-15",
    "1.0.0-14",
    "1.0.0-13",
    "1.0.0-12",
    "1.0.0-11",
    "1.0.0-10",
    "1.0.0-9",
    "1.0.0-8",
    "1.0.0-7",
    "1.0.0-6",
    "1.0.0-5",
    "1.0.0-4",
    "1.0.0-3",
    "1.0.0-2",
    "0.0.1-11",
    "0.0.1-8",
    "0.0.1-7",
    "0.0.1-6",
    "0.0.1-5",
    "0.0.1-4",
    "0.0.1-3",
    "0.0.1-2",
    "0.0.1-1",
    "0.0.0-8",
    "0.0.0-7",
    "0.0.0-6",
    "0.0.0-5",
    "0.0.0-4",
    "0.0.0-3",
    "0.0.0-2",
]


mock_apt_packages = {}

import sys


def mock_inspect_package(deb_name, version):
    package_dependencies = {}

    if version:
        package_dependencies[deb_name] = mock_apt_packages[deb_name][
            version
        ].get_dependencies()
    else:
        package_dependencies[deb_name] = mock_apt_packages[deb_name][
            "0.0.1-11"
        ].get_dependencies()

    return package_dependencies[deb_name]


@mock.patch(
    "mobros.commands.ros_install_runtime_deps.install_deps_executer.InstallRuntimeDependsExecuter.execute",
    return_value=None,
)
@mock.patch(
    "mobros.utils.utilitary.translate_package_name", return_value="ros-noetic-mobros"
)
@mock.patch(
    "mobros.utils.apt_utils.execute_shell_command",
    return_value=None,
)
@mock.patch(
    "mobros.utils.apt_utils.is_package_already_installed",
    return_value=False,
)
@mock.patch(
    "mobros.utils.apt_utils.get_package_avaiable_versions",
    return_value=DUMMY_AVAIABLE_VERSIONS,
)
@mock.patch(
    "mobros.utils.apt_utils.inspect_package",
    side_effect=mock_inspect_package,
)
@mock.patch(
    "mobros.utils.apt_utils.get_package_installed_version",
    return_value=None,
)
class TestInstallBuildDepsExecuter(unittest.TestCase):
    def test_execute_happy_path(
        self,
        mock_get_pkg_installed_version,
        mock_inspect_package,
        mock_get_versions,
        mock_is_pkg_installed,
        mock_execute_cmd,
        mock_rosdep_translate,
        mock_mobros_install_execute,
    ):
        TEST_RESOURCE_PATH_VALID = os.path.join(
            os.getcwd(),
            "tests",
            "resources",
            "test_dependencies",
            "tree_simple_valid_deps",
        )
        argparse_args = argparse.Namespace(
            workspace=TEST_RESOURCE_PATH_VALID, simulate=True
        )

        executer = InstallBuildDependsExecuter()
        executer.execute(argparse_args)

        expected_install_args = argparse.Namespace(
            y=True, pkg_list=["ros-noetic-mobros=1.2.0-3"], upgrade_installed=False
        )
        mock_mobros_install_execute.assert_called_with(expected_install_args)
