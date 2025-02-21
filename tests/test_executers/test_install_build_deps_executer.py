import argparse
import unittest
import os
import mock
from mobros.commands.ros_install_build_deps.install_deps_executer import (
    InstallBuildDependsExecuter,
)
from tests.constants import DUMMY_AVAILABLE_VERSIONS

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
    "mobros.utils.utilitary.translate_package_name", return_value=["ros-noetic-mobros"]
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
    "mobros.utils.apt_utils.get_package_available_versions",
    return_value=DUMMY_AVAILABLE_VERSIONS,
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
            y=True, pkg_list=["ros-noetic-mobros=1.2.0-3"], upgrade_installed=True
        )
        mock_mobros_install_execute.assert_called_with(expected_install_args)
