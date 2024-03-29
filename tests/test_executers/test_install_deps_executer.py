import argparse
import unittest

import mock
from mobros.commands.ros_install_runtime_deps.install_deps_executer import (
    InstallRuntimeDependsExecuter,
)
from tests.test_executers.mocks.mock_package import MockPackage
from tests.test_executers.mocks.mock_local_deb_package import DebPackage
from mobros.utils.utilitary import read_from_file, write_to_file, remove_file_if_exists
import queue
from tests.constants import DUMMY_AVAILABLE_VERSIONS


mock_apt_packages = {}

import sys

package_a = MockPackage("a")

package_a._register_dependency("a_sub_a", "version_lt", "1.0.0-0")
package_a._register_dependency("a_sub_b", "version_lt", "1.0.0-0")
package_a._register_dependency("a_sub_c", "version_lt", "1.0.0-0")

package_aa = MockPackage("a_sub_a")
package_ab = MockPackage("a_sub_b")
package_ac = MockPackage("a_sub_c")


package_ab._register_dependency("ab_sub_a", "version_lt", "1.0.0-0")
package_ab._register_dependency("ab_sub_b", "version_lt", "1.0.0-0")
package_ab._register_dependency("ab_sub_c", "version_lt", "1.0.0-0")

package_ab_a = MockPackage("ab_sub_a")
package_ab_b = MockPackage("ab_sub_b")
package_ab_c = MockPackage("ab_sub_c")
        
def mock_inspect_package(deb_name, version, upgrade_installed):
    package_dependencies = {}

    # Currently tests dont use dependencies of local debs
    if "./" in deb_name:
        return []
    
    if version:
        package_dependencies[deb_name] = mock_apt_packages[deb_name][
            version
        ].get_dependencies()
    else:
        package_dependencies[deb_name] = mock_apt_packages[deb_name][
            DUMMY_AVAILABLE_VERSIONS[0]
        ].get_dependencies()

    return package_dependencies[deb_name]


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
@mock.patch(
    "os.getuid",
    return_value=0,
)
class TestInstallDepsExecuter(unittest.TestCase):
    def test_execute_happy_path(
        self,
        mock_getui,
        mock_get_pkg_installed_version,
        mock_inspect_package,
        mock_get_versions,
        mock_is_pkg_installed,
        mock_execute_cmd,
    ):
        argparse_args = argparse.Namespace(
            y=True, pkg_list=["install","ros-noetic-package-a=0.0.1-4"], upgrade_installed=False
        )

        package_ab_c._register_dependency("abc_sub_a", "version_lt", "1.0.0-0")

        package_abc_a = MockPackage("abc_sub_a")
        package_abc_a._register_dependency("abca_sub_a", "version_lt", "1.0.0-0")

        package_abca_a = MockPackage("abca_sub_a")

        mock_apt_packages["ros-noetic-package-a"] = {}
        mock_apt_packages["ros-noetic-package-a"]["0.0.1-4"] = package_a
        mock_apt_packages["a_sub_a"] = {}
        mock_apt_packages["a_sub_a"]["0.0.1-11"] = package_aa
        mock_apt_packages["a_sub_b"] = {}
        mock_apt_packages["a_sub_b"]["0.0.1-11"] = package_ab
        mock_apt_packages["a_sub_c"] = {}
        mock_apt_packages["a_sub_c"]["0.0.1-11"] = package_ac

        mock_apt_packages["ab_sub_a"] = {}
        mock_apt_packages["ab_sub_a"]["0.0.1-11"] = package_ab_a
        mock_apt_packages["ab_sub_b"] = {}
        mock_apt_packages["ab_sub_b"]["0.0.1-11"] = package_ab_b
        mock_apt_packages["ab_sub_c"] = {}
        mock_apt_packages["ab_sub_c"]["0.0.1-11"] = package_ab_c

        mock_apt_packages["abc_sub_a"] = {}
        mock_apt_packages["abc_sub_a"]["0.0.1-11"] = package_abc_a
        mock_apt_packages["abca_sub_a"] = {}
        mock_apt_packages["abca_sub_a"]["0.0.1-11"] = package_abca_a

        executer = InstallRuntimeDependsExecuter()
        executer.execute(argparse_args)

        print(read_from_file("tree.mobtree"))

        install_order_result = read_from_file("packages.apt").split(" ")
        install_order_expected = queue.Queue()
        install_order_expected.put("abca_sub_a=0.0.1-11")
        install_order_expected.put("abc_sub_a=0.0.1-11")
        install_order_expected.put("ab_sub_c=0.0.1-11")
        install_order_expected.put("ab_sub_b=0.0.1-11")
        install_order_expected.put("ab_sub_a=0.0.1-11")
        install_order_expected.put("a_sub_c=0.0.1-11")
        install_order_expected.put("a_sub_b=0.0.1-11")
        install_order_expected.put("a_sub_a=0.0.1-11")
        install_order_expected.put("ros-noetic-package-a=0.0.1-4")

        expect_last = False
        for install_order_elem in install_order_result:
            ## this means the install order queue (whats expected) is smaller than the result
            self.assertFalse(expect_last)

            if not install_order_expected.empty():
                self.assertEqual(install_order_expected.get(), install_order_elem)
            else:
                expect_last = True

        ## this means the install order queue (whats expected) is bigger than the result
        if not install_order_expected.empty():
            self.fail()

        # RosBuildExecutor().execute(MockArgParser())

    def test_execute_with_tree_recalc_disapeared(
        self,
        mock_getui,
        mock_get_pkg_installed_version,
        mock_inspect_package,
        mock_get_versions,
        mock_is_pkg_installed,
        mock_execute_cmd,
    ):
        argparse_args = argparse.Namespace(
            y=True, pkg_list=["install","ros-noetic-package-a=0.0.1-4"], upgrade_installed=False
        )

        package_aa._register_dependency("abc_sub_a", "version_lte", "1.0.0-2")

        package_ab_c._register_dependency("abc_sub_a", "version_lt", "1.0.0-0")

        package_abc_a = MockPackage("abc_sub_a")
        package_abc_a._register_dependency("abcaa_sub_a", "version_lt", "1.0.0-0")

        package_abc_a2 = MockPackage("abc_sub_a")

        package_abca_a = MockPackage("abca_sub_a")
        package_abcaa_a = MockPackage("abcaa_sub_a")

        mock_apt_packages["ros-noetic-package-a"] = {}
        mock_apt_packages["ros-noetic-package-a"]["0.0.1-4"] = package_a
        mock_apt_packages["a_sub_a"] = {}
        mock_apt_packages["a_sub_a"]["0.0.1-11"] = package_aa
        mock_apt_packages["a_sub_b"] = {}
        mock_apt_packages["a_sub_b"]["0.0.1-11"] = package_ab
        mock_apt_packages["a_sub_c"] = {}
        mock_apt_packages["a_sub_c"]["0.0.1-11"] = package_ac
        mock_apt_packages["ab_sub_a"] = {}
        mock_apt_packages["ab_sub_a"]["0.0.1-11"] = package_ab_a
        mock_apt_packages["ab_sub_b"] = {}
        mock_apt_packages["ab_sub_b"]["0.0.1-11"] = package_ab_b
        mock_apt_packages["ab_sub_c"] = {}
        mock_apt_packages["ab_sub_c"]["0.0.1-11"] = package_ab_c

        mock_apt_packages["abc_sub_a"] = {}
        mock_apt_packages["abc_sub_a"]["1.0.0-2"] = package_abc_a
        mock_apt_packages["abc_sub_a"]["0.0.1-11"] = package_abc_a2

        mock_apt_packages["abca_sub_a"] = {}
        mock_apt_packages["abca_sub_a"]["0.0.1-11"] = package_abca_a

        mock_apt_packages["abcaa_sub_a"] = {}
        mock_apt_packages["abcaa_sub_a"]["0.0.1-11"] = package_abcaa_a

        executer = InstallRuntimeDependsExecuter()
        executer.execute(argparse_args)

        print(read_from_file("tree.mobtree"))

        install_order_result = read_from_file("packages.apt").split(" ")
        install_order_expected = queue.Queue()

        install_order_expected.put("abc_sub_a=0.0.1-11")
        install_order_expected.put("ab_sub_c=0.0.1-11")
        install_order_expected.put("ab_sub_b=0.0.1-11")
        install_order_expected.put("ab_sub_a=0.0.1-11")

        install_order_expected.put("a_sub_c=0.0.1-11")
        install_order_expected.put("a_sub_b=0.0.1-11")
        install_order_expected.put("a_sub_a=0.0.1-11")
        install_order_expected.put("ros-noetic-package-a=0.0.1-4")

        expect_last = False
        for install_order_elem in install_order_result:
            ## this means the install order queue (whats expected) is smaller than the result
            self.assertFalse(expect_last)

            if not install_order_expected.empty():
                self.assertEqual(install_order_expected.get(), install_order_elem)
            else:
                expect_last = True

        ## this means the install order queue (whats expected) is bigger than the result
        if not install_order_expected.empty():
            self.fail()

    #        self.fail()
    # RosBuildExecutor().execute(MockArgParser())

    def test_execute_with_tree_recalc_full_sub_tree_recalc(
        self,
        mock_getui,
        mock_get_pkg_installed_version,
        mock_inspect_package,
        mock_get_versions,
        mock_is_pkg_installed,
        mock_execute_cmd,
    ):
        argparse_args = argparse.Namespace(
            y=True, pkg_list=["install", "ros-noetic-package-a=0.0.1-4"], upgrade_installed=False
        )

        package_aa._register_dependency("abc_sub_a", "version_lte", "1.0.0-2")

        package_ab_c._register_dependency("abcc_sub_c", "version_eq", "0.0.1-11")

        package_abc_a = MockPackage("abc_sub_a")
        package_abc_a._register_dependency("abcaa_sub_a", "version_lt", "1.0.0-0")

        package_abc_a2 = MockPackage("abc_sub_a")
        package_abc_a2._register_dependency("abca2_sub_a", "version_eq", "0.0.1-11")
        package_abc_a2._register_dependency("abca2_sub_b", "version_eq", "0.0.1-11")

        package_abcc_a = MockPackage("abcc_sub_c")
        package_abcc_a._register_dependency("abccc_sub_c", "version_eq", "0.0.1-11")

        package_abccc_a = MockPackage("abccc_sub_c")
        package_abccc_a._register_dependency("abc_sub_a", "version_lt", "1.0.0-0")

        package_abca_a = MockPackage("abca_sub_a")
        package_abcaa_a = MockPackage("abcaa_sub_a")

        package_abca2_a = MockPackage("abca2_sub_a")
        package_abca2_b = MockPackage("abca2_sub_b")

        mock_apt_packages["ros-noetic-package-a"] = {}
        mock_apt_packages["ros-noetic-package-a"]["0.0.1-4"] = package_a
        mock_apt_packages["a_sub_a"] = {}
        mock_apt_packages["a_sub_a"]["0.0.1-11"] = package_aa
        mock_apt_packages["a_sub_b"] = {}
        mock_apt_packages["a_sub_b"]["0.0.1-11"] = package_ab
        mock_apt_packages["a_sub_c"] = {}
        mock_apt_packages["a_sub_c"]["0.0.1-11"] = package_ac
        mock_apt_packages["ab_sub_a"] = {}
        mock_apt_packages["ab_sub_a"]["0.0.1-11"] = package_ab_a
        mock_apt_packages["ab_sub_b"] = {}
        mock_apt_packages["ab_sub_b"]["0.0.1-11"] = package_ab_b
        mock_apt_packages["ab_sub_c"] = {}
        mock_apt_packages["ab_sub_c"]["0.0.1-11"] = package_ab_c

        mock_apt_packages["abc_sub_a"] = {}
        mock_apt_packages["abc_sub_a"]["1.0.0-2"] = package_abc_a
        mock_apt_packages["abc_sub_a"]["0.0.1-11"] = package_abc_a2

        mock_apt_packages["abca_sub_a"] = {}
        mock_apt_packages["abca_sub_a"]["0.0.1-11"] = package_abca_a

        mock_apt_packages["abcaa_sub_a"] = {}
        mock_apt_packages["abcaa_sub_a"]["0.0.1-11"] = package_abcaa_a

        mock_apt_packages["abca2_sub_a"] = {}
        mock_apt_packages["abca2_sub_a"]["0.0.1-11"] = package_abca2_a
        mock_apt_packages["abca2_sub_b"] = {}
        mock_apt_packages["abca2_sub_b"]["0.0.1-11"] = package_abca2_b

        mock_apt_packages["abcc_sub_c"] = {}
        mock_apt_packages["abcc_sub_c"]["0.0.1-11"] = package_abcc_a
        mock_apt_packages["abccc_sub_c"] = {}
        mock_apt_packages["abccc_sub_c"]["0.0.1-11"] = package_abccc_a

        executer = InstallRuntimeDependsExecuter()
        executer.execute(argparse_args)

        print(read_from_file("tree.mobtree"))

        install_order_result = read_from_file("packages.apt").split(" ")
        install_order_expected = queue.Queue()
        install_order_expected.put("abca2_sub_b=0.0.1-11")
        install_order_expected.put("abca2_sub_a=0.0.1-11")
        install_order_expected.put("abccc_sub_c=0.0.1-11")
        install_order_expected.put("abcc_sub_c=0.0.1-11")
        install_order_expected.put("abc_sub_a=0.0.1-11")
        install_order_expected.put("ab_sub_c=0.0.1-11")
        install_order_expected.put("ab_sub_b=0.0.1-11")
        install_order_expected.put("ab_sub_a=0.0.1-11")

        install_order_expected.put("a_sub_c=0.0.1-11")
        install_order_expected.put("a_sub_b=0.0.1-11")
        install_order_expected.put("a_sub_a=0.0.1-11")
        install_order_expected.put("ros-noetic-package-a=0.0.1-4")

        expect_last = False
        for install_order_elem in install_order_result:
            ## this means the install order queue (whats expected) is smaller than the result
            self.assertFalse(expect_last)

            if not install_order_expected.empty():
                self.assertEqual(install_order_expected.get(), install_order_elem)
            else:
                expect_last = True

        ## this means the install order queue (whats expected) is bigger than the result
        if not install_order_expected.empty():
            self.fail()
        # RosBuildExecutor().execute(MockArgParser())

    def test_execute_full_install_no_version_specified(
        self,
        mock_getui,
        mock_get_pkg_installed_version,
        mock_inspect_package,
        mock_get_versions,
        mock_is_pkg_installed,
        mock_execute_cmd,
    ):
        argparse_args = argparse.Namespace(
            y=True, pkg_list=["install","ros-noetic-package-a=0.0.1-4", "ros-noetic-package-solo"], upgrade_installed=False
        )
        mock_apt_packages["ros-noetic-package-solo"] = {}
        mock_apt_packages["ros-noetic-package-solo"]["2.0.0-8"] = package_ab_b
        

        mock_apt_packages["ros-noetic-package-a"] = {}
        mock_apt_packages["ros-noetic-package-a"]["0.0.1-4"] = package_ab_a

        executer = InstallRuntimeDependsExecuter()
        executer.execute(argparse_args)

        print(read_from_file("tree.mobtree"))

        install_order_result = read_from_file("packages.apt").split(" ")
        install_order_expected = queue.Queue()
        install_order_expected.put("ros-noetic-package-a=0.0.1-4")
        install_order_expected.put("ros-noetic-package-solo=2.0.0-8")

        expect_last = False
        for install_order_elem in install_order_result:
            ## this means the install order queue (whats expected) is smaller than the result
            self.assertFalse(expect_last)

            if not install_order_expected.empty():
                self.assertEqual(install_order_expected.get(), install_order_elem)
            else:
                expect_last = True

        ## this means the install order queue (whats expected) is bigger than the result
        if not install_order_expected.empty():
            self.fail()

    @mock.patch(
    "apt.debfile.DebPackage",
    side_effect=DebPackage,
    )
    def test_execute_full_install_local_deb(
        self,
        mock_deb_pkg,
        mock_getui,
        mock_get_pkg_installed_version,
        mock_inspect_package,
        mock_get_versions,
        mock_is_pkg_installed,
        mock_execute_cmd,
    ):
        remove_file_if_exists("./ros-noetic-package-solo.deb")
        write_to_file("./ros-noetic-package-solo.deb", "dummy")
        
        argparse_args = argparse.Namespace(
            y=True, pkg_list=["install","ros-noetic-package-a=0.0.1-4", "./ros-noetic-package-solo.deb"], upgrade_installed=False
        )

        mock_apt_packages["ros-noetic-package-solo"] = {}
        mock_apt_packages["ros-noetic-package-solo"]["2.0.0-8"] = package_ab_b

        mock_apt_packages["ros-noetic-package-a"] = {}
        mock_apt_packages["ros-noetic-package-a"]["0.0.1-4"] = package_ab_a

        executer = InstallRuntimeDependsExecuter()
        executer.execute(argparse_args)

        print(read_from_file("tree.mobtree"))

        install_order_result = read_from_file("packages.apt").split(" ")
        install_order_expected = queue.Queue()
        install_order_expected.put("ros-noetic-package-a=0.0.1-4")
        install_order_expected.put("./ros-noetic-package-solo.deb")

        expect_last = False
        for install_order_elem in install_order_result:
            ## this means the install order queue (whats expected) is smaller than the result
            self.assertFalse(expect_last)

            if not install_order_expected.empty():
                self.assertEqual(install_order_expected.get(), install_order_elem)
            else:
                expect_last = True

        ## this means the install order queue (whats expected) is bigger than the result
        if not install_order_expected.empty():
            self.fail()
