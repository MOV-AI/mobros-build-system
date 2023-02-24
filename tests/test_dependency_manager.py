import os
import unittest

import mock

from mobros.commands.ros_install_build_deps.catkin_package import CatkinPackage
from mobros.dependency_manager.dependency_manager import (
    DependencyManager,
    find_candidate_online,
    find_equals_rule,
    find_highest_bottom_rule,
    find_lowest_top_rule,
)
from mobros.exceptions import InstallCandidateNotFoundException
from tests.test_executors.mocks.mock_package import MockPackage
from mobros.types.intternal_package import PackageInterface 

def load_test_resource_workspace(WORKSPACE_NAME):
    dep_manager = DependencyManager()
    TEST_RESOURCE_PATH_VALID = os.path.join(
        os.getcwd(), "tests", "resources", "test_dependencies", WORKSPACE_NAME
    )
    for path, _, files in os.walk(TEST_RESOURCE_PATH_VALID):
        for name in files:
            if name == "package.xml":
                package = CatkinPackage(os.path.join(path, name))
                dep_manager.register_package(package)

    return dep_manager


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


class TestDependencyManagerColisions(unittest.TestCase):
    @mock.patch("mobros.utils.utilitary.execute_shell_command", return_value=["ros-noetic-ompl"])
    def test_register_package(self, mock):
        dep_manager = load_test_resource_workspace("tree_simple_valid_deps")
        print(dep_manager._dependency_bank)
        dependency = dep_manager._dependency_bank["ros-noetic-ompl"][0]
        self.assertEqual(dependency["from"], "package_a")
        self.assertEqual(dependency["operator"], "version_lte")
        self.assertEqual(dependency["version"], "1.5.2-6")

    def test_exclude_package(self):
        dep_manager = DependencyManager()
        TEST_KEY = "test"
        TEST_EXCLUDED_KEY = "test_exclude"
        dep_manager._dependency_bank[TEST_KEY] = []
        dep_manager._dependency_bank[TEST_EXCLUDED_KEY] = []
        self.assertEqual(dep_manager._dependency_bank[TEST_EXCLUDED_KEY], [])
        dep_manager.exclude_package(TEST_EXCLUDED_KEY)
        self.assertFalse(TEST_EXCLUDED_KEY in dep_manager._dependency_bank)
        self.assertEqual(dep_manager._dependency_bank[TEST_KEY], [])

    @mock.patch("mobros.utils.utilitary.execute_shell_command", return_value=["ros-noetoc-mobros"])
    def test_conflict_detection_edges_clash(self, mock_execute_shell):
        dep_manager = load_test_resource_workspace("tree_conflict_edges")

        with self.assertRaises(SystemExit) as method_execution_exit:
            dep_manager.check_colisions()

        self.assertEqual(method_execution_exit.exception.code, 1)

    @mock.patch("mobros.utils.utilitary.execute_shell_command", return_value=["ros-noetoc-mobros"])
    def test_conflict_detection_multi_equals_clash(self, mock_execute_shell):
        dep_manager = load_test_resource_workspace("tree_conflict_equals_clash")

        with self.assertRaises(SystemExit) as method_execution_exit:
            dep_manager.check_colisions()

        self.assertEqual(method_execution_exit.exception.code, 1)

    @mock.patch("mobros.utils.utilitary.execute_shell_command", return_value=["ros-noetoc-mobros"])
    def test_conflict_detection_equals_top_clash(self, mock_execute_shell):
        dep_manager = load_test_resource_workspace("tree_conflict_equals_top")

        with self.assertRaises(SystemExit) as method_execution_exit:
            dep_manager.check_colisions()

        self.assertEqual(method_execution_exit.exception.code, 1)

    @mock.patch("mobros.utils.utilitary.execute_shell_command", return_value=["ros-noetoc-mobros"])
    def test_conflict_detection_equals_bottom_clash(self, mock_execute_shell):
        dep_manager = load_test_resource_workspace("tree_conflict_equals_bottom")

        with self.assertRaises(SystemExit) as method_execution_exit:
            dep_manager.check_colisions()

        self.assertEqual(method_execution_exit.exception.code, 1)

    @mock.patch("mobros.utils.utilitary.execute_shell_command", return_value=["ros-noetoc-mobros"])
    def test_conflict_valid_bottom_inclusion(self, mock_execute_shell):
        dep_manager = load_test_resource_workspace("tree_valid_bottom_inclusion")

        dep_manager.check_colisions()

    @mock.patch("mobros.utils.utilitary.execute_shell_command", return_value=["ros-noetoc-mobros"])
    def test_conflict_valid_top_inclusion(self, mock_execute_shell):
        dep_manager = load_test_resource_workspace("tree_valid_top_inclusion")

        dep_manager.check_colisions()

    def test_find_highest_bottom_rule(self):
        version_rules = []
        version_rules.append(
            {"version": "0.2.0-7000", "operator": "version_gte", "from": "dummy"}
        )
        version_rules.append(
            {"version": "0.900.0-0", "operator": "version_gte", "from": "dummy"}
        )
        version_rules.append(
            {"version": "4.0.900-0", "operator": "version_gt", "from": "dummy"}
        )
        version_rules.append(
            {"version": "0.900.0-0", "operator": "version_lte", "from": "dummy"}
        )
        version_rules.append(
            {"version": "1.0.0-0", "operator": "version_gt", "from": "dummy"}
        )
        highest_bottom = find_highest_bottom_rule(version_rules)
        self.assertEqual(highest_bottom["version"], "4.0.900-0")
        self.assertEqual(highest_bottom["included"], False)

        version_rules = []
        version_rules.append(
            {"version": "0.2.0-7000", "operator": "version_gte", "from": "dummy"}
        )
        version_rules.append(
            {"version": "0.900.0-0", "operator": "version_gte", "from": "dummy"}
        )
        version_rules.append(
            {"version": "4.0.900-0", "operator": "version_gte", "from": "dummy"}
        )
        version_rules.append(
            {"version": "0.900.0-0", "operator": "version_lte", "from": "dummy"}
        )
        version_rules.append(
            {"version": "1.0.0-0", "operator": "version_gt", "from": "dummy"}
        )
        highest_bottom = find_highest_bottom_rule(version_rules)
        self.assertEqual(highest_bottom["version"], "4.0.900-0")
        self.assertEqual(highest_bottom["included"], True)

    def test_find_lowest_top_rule(self):
        version_rules = []
        version_rules.append(
            {"version": "0.2.0-7000", "operator": "version_lte", "from": "dummy"}
        )
        version_rules.append(
            {"version": "0.900.0-0", "operator": "version_lte", "from": "dummy"}
        )
        version_rules.append(
            {"version": "4.0.900-0", "operator": "version_lt", "from": "dummy"}
        )
        version_rules.append(
            {"version": "4.0.900-0", "operator": "version_gt", "from": "dummy"}
        )
        version_rules.append(
            {"version": "1.0.0-0", "operator": "version_lt", "from": "dummy"}
        )
        lowest_top = find_lowest_top_rule(version_rules)
        self.assertEqual(lowest_top["version"], "0.2.0-7000")
        self.assertEqual(lowest_top["included"], True)

        version_rules = []
        version_rules.append(
            {"version": "0.2.0-7000", "operator": "version_lt", "from": "dummy"}
        )
        version_rules.append(
            {"version": "0.900.0-0", "operator": "version_lte", "from": "dummy"}
        )
        version_rules.append(
            {"version": "4.0.900-0", "operator": "version_lt", "from": "dummy"}
        )
        version_rules.append(
            {"version": "4.0.900-0", "operator": "version_gt", "from": "dummy"}
        )
        version_rules.append(
            {"version": "1.0.0-0", "operator": "version_lt", "from": "dummy"}
        )
        lowest_top = find_lowest_top_rule(version_rules)
        self.assertEqual(lowest_top["version"], "0.2.0-7000")
        self.assertEqual(lowest_top["included"], False)

    def test_find_equals_rule(self):
        version_rules = []
        version_rules.append(
            {"version": "0.2.0-7000", "operator": "version_lte", "from": "dummy"}
        )
        version_rules.append(
            {"version": "0.900.0-0", "operator": "version_lte", "from": "dummy"}
        )
        version_rules.append(
            {"version": "4.0.900-0", "operator": "version_lt", "from": "dummy"}
        )
        version_rules.append(
            {"version": "1.0.0-0", "operator": "version_lt", "from": "dummy"}
        )
        version_rules.append(
            {"version": "1.0.0-0", "operator": "version_eq", "from": "dummy"}
        )
        found, equals_rule_found = find_equals_rule(version_rules)
        self.assertTrue(found)
        self.assertEqual(equals_rule_found["version"], "1.0.0-0")

    def test_find_equals_rule_not_found(self):
        version_rules = []
        version_rules.append(
            {"version": "0.2.0-7000", "operator": "version_lte", "from": "dummy"}
        )
        version_rules.append(
            {"version": "0.900.0-0", "operator": "version_lte", "from": "dummy"}
        )
        version_rules.append(
            {"version": "4.0.900-0", "operator": "version_lt", "from": "dummy"}
        )
        version_rules.append(
            {"version": "1.0.0-0", "operator": "version_lt", "from": "dummy"}
        )
        version_rules.append(
            {"version": "1.0.0-0", "operator": "version_gt", "from": "dummy"}
        )
        found, equals_rule_found = find_equals_rule(version_rules)
        self.assertFalse(found)
        self.assertIsNone(equals_rule_found)

    @mock.patch("mobros.utils.apt_utils.get_package_avaiable_versions", return_value=[])
    def test_find_candidate_online_no_online_candidates(
        self, mock_get_avaiable_versions
    ):
        with self.assertRaises(InstallCandidateNotFoundException):
            find_candidate_online("ros-noetic-mobros", [])
        #self.assertEqual(executionException.message, False)

    @mock.patch("mobros.utils.apt_utils.get_package_avaiable_versions", return_value=["2.0.0-0"])
    def test_find_candidate_online_equals_not_avaiable_online(
        self, mock_get_avaiable_versions
    ):

        version_rules = []
        version_rules.append(
            {"version": "1.0.0-0", "operator": "version_eq", "from": "dummy"}
        )

        with self.assertRaises(InstallCandidateNotFoundException):
            find_candidate_online("ros-noetic-mobros", version_rules)            

        #self.assertEqual(method_execution_exit.exception.code, 1)

    @mock.patch("mobros.utils.apt_utils.get_package_avaiable_versions", return_value=["2.0.0-0"])
    def test_find_candidate_online_bottom_rule_not_avaiable_online(
        self, mock_get_avaiable_versions
    ):

        version_rules = []
        version_rules.append(
            {"version": "1.0.0-0", "operator": "version_lt", "from": "dummy"}
        )

        with self.assertRaises(InstallCandidateNotFoundException):
            find_candidate_online("ros-noetic-mobros", version_rules)

        #self.assertEqual(method_execution_exit.exception.code, 1)

    @mock.patch("mobros.utils.apt_utils.get_package_avaiable_versions", return_value=["2.0.0-0"])
    def test_find_candidate_online_top_rule_not_avaiable_online(
        self, mock_get_avaiable_versions
    ):

        version_rules = []
        version_rules.append(
            {"version": "3.0.0-0", "operator": "version_gt", "from": "dummy"}
        )

        with self.assertRaises(InstallCandidateNotFoundException):
            find_candidate_online("ros-noetic-mobros", version_rules)

        #self.assertEqual(method_execution_exit.exception.code, 1)

    @mock.patch(
        "mobros.utils.apt_utils.get_package_avaiable_versions",
        return_value=DUMMY_AVAIABLE_VERSIONS,
    )
    def test_find_candidate_online_edges(self, mock_get_avaiable_versions):
        version_rules = []
        version_rules.append(
            {"version": "1.0.0-0", "operator": "version_gt", "from": "dummy2"}
        )
        version_rules.append(
            {"version": "2.0.0-0", "operator": "version_lte", "from": "dummy"}
        )

        version = find_candidate_online("ros-noetic-mobros", version_rules)
        self.assertEqual(version, "1.2.0-3")

        version_rules = []
        version_rules.append(
            {"version": "1.0.0-0", "operator": "version_gt", "from": "dummy2"}
        )
        version_rules.append(
            {"version": "1.0.2-1", "operator": "version_gte", "from": "dummy2"}
        )
        version_rules.append(
            {"version": "2.0.0-3", "operator": "version_lte", "from": "dummy"}
        )

        version = find_candidate_online("ros-noetic-mobros", version_rules)
        self.assertEqual(version, "2.0.0-3")

    @mock.patch(
        "mobros.utils.apt_utils.get_package_avaiable_versions",
        return_value=DUMMY_AVAIABLE_VERSIONS,
    )
    def test_find_candidate_online_specific_equals(self, mock_get_avaiable_versions):
        version_rules = []
        version_rules.append(
            {"version": "1.0.0-55", "operator": "version_eq", "from": "dummy"}
        )
        version = find_candidate_online("ros-noetic-mobros", version_rules)
        self.assertEqual(version, "1.0.0-55")

        version_rules = []
        version_rules.append(
            {"version": "2.0.0-3", "operator": "version_eq", "from": "dummy"}
        )
        version = find_candidate_online("ros-noetic-mobros", version_rules)
        self.assertEqual(version, "2.0.0-3")

        version_rules = []
        version_rules.append(
            {"version": "0.0.0-5", "operator": "version_eq", "from": "dummy"}
        )
        version = find_candidate_online("ros-noetic-mobros", version_rules)
        self.assertEqual(version, "0.0.0-5")

class TestDependencyManagerIntegration(unittest.TestCase):

    def test_mock(self):

        if not issubclass(MockPackage, PackageInterface):
            self.fail()

    @mock.patch(
        "mobros.utils.apt_utils.get_package_avaiable_versions",
        return_value=DUMMY_AVAIABLE_VERSIONS,
    )
    def test_clean_colision_reset_after_evaluation(self, mock_get_avaiable_versions):
        dep_manager = DependencyManager()

        package_a = MockPackage("a")
        
        package_a._register_dependency("a_sub_a","version_lt","1.0.0-0")

        dep_manager.register_package(package_a)
        self.assertIn("a_sub_a", dep_manager._possible_colision)
        self.assertIn("a_sub_a", dep_manager._possible_install_candidate_compromised)

        dep_manager.check_colisions()
        self.assertNotIn("a_sub_a", dep_manager._possible_colision)
        self.assertIn("a_sub_a", dep_manager._possible_install_candidate_compromised)

        dep_manager.calculate_installs()
        self.assertNotIn("a_sub_a", dep_manager._possible_colision)
        self.assertNotIn("a_sub_a", dep_manager._possible_install_candidate_compromised)

    @mock.patch(
        "mobros.utils.apt_utils.get_package_avaiable_versions",
        return_value=DUMMY_AVAIABLE_VERSIONS,
    )
    def test_tree_recalc_skip_event(self, mock_get_avaiable_versions):
        
        dep_manager = DependencyManager()

        package_a = MockPackage("a")
        
        package_a._register_dependency("a_sub_a","version_lt","1.0.0-0")
        package_a._register_dependency("a_sub_b","version_lt","1.0.0-0")
        package_a._register_dependency("a_sub_c","version_lt","1.0.0-0")

        dep_manager.register_package(package_a)
        dep_manager.calculate_installs()

        package_ab = MockPackage("a_sub_b")
        package_ab._register_dependency("ab_sub_a","version_gt","1.0.0-0")
        package_ab._register_dependency("ab_sub_b","version_gt","1.0.0-0")
        package_ab._register_dependency("ab_sub_c","version_gte","1.0.0-0")

        dep_manager.register_package(package_ab)
        dep_manager.calculate_installs()

        package_abb = MockPackage("ab_sub_b")
        package_abb._register_dependency("abb_sub_a","version_gt","1.0.0-0")
        package_abb._register_dependency("abb_sub_b","version_gt","1.0.0-0")
        package_abb._register_dependency("abb_sub_c","version_gte","1.0.0-0")

        dep_manager.register_package(package_abb)
        dep_manager.calculate_installs()

        dep_manager.render_tree(True)
        self.assertNotIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

        package_shared_dep1 = MockPackage("shared_dep")
        package_shared_dep1._register_dependency("ab_sub_b","version_eq","2.0.0-8")
        dep_manager.register_package(package_shared_dep1)
        dep_manager.render_tree(True)
        self.assertNotIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

        package_shared_dep2 = MockPackage("shared_dep3")
        package_shared_dep2._register_dependency("ab_sub_b","version_lte","2.0.0-8")
        dep_manager.register_package(package_shared_dep2)
        dep_manager.render_tree(True)
        self.assertNotIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

        package_shared_dep3 = MockPackage("shared_dep3")
        package_shared_dep3._register_dependency("ab_sub_b","version_lt","2.0.0-9")
        dep_manager.register_package(package_shared_dep3)
        dep_manager.render_tree(True)
        self.assertNotIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

        package_shared_dep4 = MockPackage("shared_dep4")
        package_shared_dep4._register_dependency("ab_sub_b","version_gte","2.0.0-8")
        dep_manager.register_package(package_shared_dep3)
        dep_manager.render_tree(True)
        self.assertNotIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

    @mock.patch(
        "mobros.utils.apt_utils.get_package_avaiable_versions",
        return_value=DUMMY_AVAIABLE_VERSIONS,
    )
    def test_tree_recalc_compromise_event_gt(self, mock_get_avaiable_versions):
        
        dep_manager = DependencyManager()

        package_a = MockPackage("a")
        
        package_a._register_dependency("a_sub_a","version_lt","1.0.0-0")
        package_a._register_dependency("a_sub_b","version_lt","1.0.0-0")
        package_a._register_dependency("a_sub_c","version_lt","1.0.0-0")

        dep_manager.register_package(package_a)
        dep_manager.calculate_installs()

        package_ab = MockPackage("a_sub_b")
        package_ab._register_dependency("ab_sub_a","version_gt","1.0.0-0")
        package_ab._register_dependency("ab_sub_b","version_gt","1.0.0-0")
        package_ab._register_dependency("ab_sub_c","version_gte","1.0.0-0")

        dep_manager.register_package(package_ab)
        dep_manager.calculate_installs()

        package_abb = MockPackage("ab_sub_b")
        package_abb._register_dependency("abb_sub_a","version_gt","1.0.0-0")
        package_abb._register_dependency("abb_sub_b","version_gt","1.0.0-0")
        package_abb._register_dependency("abb_sub_c","version_gte","1.0.0-0")

        dep_manager.register_package(package_abb)
        dep_manager.calculate_installs()

        dep_manager.render_tree(True)
        self.assertNotIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

        package_shared = MockPackage("shared")
        package_shared._register_dependency("ab_sub_b","version_gt","2.0.0-7")
        dep_manager.register_package(package_shared)
        dep_manager.render_tree(True)
        self.assertNotIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

        package_colider = MockPackage("colider")
        package_colider._register_dependency("ab_sub_b","version_gt","2.0.0-8")
        dep_manager.register_package(package_colider)
        dep_manager.render_tree(True)
        self.assertIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

    @mock.patch(
        "mobros.utils.apt_utils.get_package_avaiable_versions",
        return_value=DUMMY_AVAIABLE_VERSIONS,
    )
    def test_tree_recalc_compromise_event_gte(self, mock_get_avaiable_versions):
        
        dep_manager = DependencyManager()

        package_a = MockPackage("a")
        
        package_a._register_dependency("a_sub_a","version_lt","1.0.0-0")
        package_a._register_dependency("a_sub_b","version_lt","1.0.0-0")
        package_a._register_dependency("a_sub_c","version_lt","1.0.0-0")

        dep_manager.register_package(package_a)
        dep_manager.calculate_installs()

        package_ab = MockPackage("a_sub_b")
        package_ab._register_dependency("ab_sub_a","version_gt","1.0.0-0")
        package_ab._register_dependency("ab_sub_b","version_gt","1.0.0-0")
        package_ab._register_dependency("ab_sub_c","version_gte","1.0.0-0")

        dep_manager.register_package(package_ab)
        dep_manager.calculate_installs()

        package_abb = MockPackage("ab_sub_b")
        package_abb._register_dependency("abb_sub_a","version_gt","1.0.0-0")
        package_abb._register_dependency("abb_sub_b","version_gt","1.0.0-0")
        package_abb._register_dependency("abb_sub_c","version_gte","1.0.0-0")

        dep_manager.register_package(package_abb)
        dep_manager.calculate_installs()

        dep_manager.render_tree(True)
        self.assertNotIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

        package_shared = MockPackage("shared")
        package_shared._register_dependency("ab_sub_b","version_gte","2.0.0-8")
        dep_manager.register_package(package_shared)
        dep_manager.render_tree(True)
        self.assertNotIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

        package_colider = MockPackage("colider")
        package_colider._register_dependency("ab_sub_b","version_gte","2.0.0-9")
        dep_manager.register_package(package_colider)
        dep_manager.render_tree(True)
        self.assertIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

    @mock.patch(
        "mobros.utils.apt_utils.get_package_avaiable_versions",
        return_value=DUMMY_AVAIABLE_VERSIONS,
    )
    def test_tree_recalc_compromise_event_lt(self, mock_get_avaiable_versions):
        
        dep_manager = DependencyManager()

        package_a = MockPackage("a")
        
        package_a._register_dependency("a_sub_a","version_lt","1.0.0-0")
        package_a._register_dependency("a_sub_b","version_lt","1.0.0-0")
        package_a._register_dependency("a_sub_c","version_lt","1.0.0-0")

        dep_manager.register_package(package_a)
        dep_manager.calculate_installs()

        package_ab = MockPackage("a_sub_b")
        package_ab._register_dependency("ab_sub_a","version_gt","1.0.0-0")
        package_ab._register_dependency("ab_sub_b","version_gt","1.0.0-0")
        package_ab._register_dependency("ab_sub_c","version_gte","1.0.0-0")

        dep_manager.register_package(package_ab)
        dep_manager.calculate_installs()

        package_abb = MockPackage("ab_sub_b")
        package_abb._register_dependency("abb_sub_a","version_gt","1.0.0-0")
        package_abb._register_dependency("abb_sub_b","version_gt","1.0.0-0")
        package_abb._register_dependency("abb_sub_c","version_gte","1.0.0-0")

        dep_manager.register_package(package_abb)
        dep_manager.calculate_installs()

        dep_manager.render_tree(True)
        self.assertNotIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

        package_shared = MockPackage("shared")
        package_shared._register_dependency("ab_sub_b","version_lt","2.0.0-9")
        dep_manager.register_package(package_shared)
        self.assertNotIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

        package_colider = MockPackage("colider")
        package_colider._register_dependency("ab_sub_b","version_lt","2.0.0-8")
        dep_manager.register_package(package_colider)
        dep_manager.render_tree(True)
        self.assertIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

    @mock.patch(
        "mobros.utils.apt_utils.get_package_avaiable_versions",
        return_value=DUMMY_AVAIABLE_VERSIONS,
    )
    def test_tree_recalc_compromise_event_lte(self, mock_get_avaiable_versions):
        
        dep_manager = DependencyManager()

        package_a = MockPackage("a")
        
        package_a._register_dependency("a_sub_a","version_lt","1.0.0-0")
        package_a._register_dependency("a_sub_b","version_lt","1.0.0-0")
        package_a._register_dependency("a_sub_c","version_lt","1.0.0-0")

        dep_manager.register_package(package_a)
        dep_manager.calculate_installs()

        package_ab = MockPackage("a_sub_b")
        package_ab._register_dependency("ab_sub_a","version_gt","1.0.0-0")
        package_ab._register_dependency("ab_sub_b","version_gt","1.0.0-0")
        package_ab._register_dependency("ab_sub_c","version_gte","1.0.0-0")

        dep_manager.register_package(package_ab)
        dep_manager.calculate_installs()

        package_abb = MockPackage("ab_sub_b")
        package_abb._register_dependency("abb_sub_a","version_gt","1.0.0-0")
        package_abb._register_dependency("abb_sub_b","version_gt","1.0.0-0")
        package_abb._register_dependency("abb_sub_c","version_gte","1.0.0-0")

        dep_manager.register_package(package_abb)
        dep_manager.calculate_installs()

        dep_manager.render_tree(True)
        self.assertNotIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

        package_shared = MockPackage("shared")
        package_shared._register_dependency("ab_sub_b","version_lte","2.0.0-9")
        dep_manager.register_package(package_shared)
        dep_manager.render_tree(True)
        self.assertNotIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

        package_colider = MockPackage("colider")
        package_colider._register_dependency("ab_sub_b","version_lte","2.0.0-7")
        dep_manager.register_package(package_colider)
        dep_manager.render_tree(True)
        self.assertIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

    @mock.patch(
        "mobros.utils.apt_utils.get_package_avaiable_versions",
        return_value=DUMMY_AVAIABLE_VERSIONS,
    )
    def test_tree_recalc_compromise_event_eq(self, mock_get_avaiable_versions):
        
        dep_manager = DependencyManager()

        package_a = MockPackage("a")
        
        package_a._register_dependency("a_sub_a","version_lt","1.0.0-0")
        package_a._register_dependency("a_sub_b","version_lt","1.0.0-0")
        package_a._register_dependency("a_sub_c","version_lt","1.0.0-0")

        dep_manager.register_package(package_a)
        dep_manager.calculate_installs()

        package_ab = MockPackage("a_sub_b")
        package_ab._register_dependency("ab_sub_a","version_gt","1.0.0-0")
        package_ab._register_dependency("ab_sub_b","version_gt","1.0.0-0")
        package_ab._register_dependency("ab_sub_c","version_gte","1.0.0-0")

        dep_manager.register_package(package_ab)
        dep_manager.calculate_installs()

        package_abb = MockPackage("ab_sub_b")
        package_abb._register_dependency("abb_sub_a","version_gt","1.0.0-0")
        package_abb._register_dependency("abb_sub_b","version_gt","1.0.0-0")
        package_abb._register_dependency("abb_sub_c","version_gte","1.0.0-0")

        dep_manager.register_package(package_abb)
        dep_manager.calculate_installs()

        dep_manager.render_tree(True)
        self.assertNotIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

        package_shared = MockPackage("shared")
        package_shared._register_dependency("ab_sub_b","version_eq","2.0.0-8")
        dep_manager.register_package(package_shared)
        dep_manager.render_tree(True)
        self.assertNotIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

        package_colider = MockPackage("colider")
        package_colider._register_dependency("ab_sub_b","version_eq","2.0.0-7")
        dep_manager.register_package(package_colider)
        dep_manager.render_tree(True)
        self.assertIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

    @mock.patch(
        "mobros.utils.apt_utils.get_package_avaiable_versions",
        return_value=DUMMY_AVAIABLE_VERSIONS,
    )
    def test_tree_recalc_tree(self, mock_get_avaiable_versions):
        
        dep_manager = DependencyManager()

        package_a = MockPackage("a")
        
        package_a._register_dependency("a_sub_a","version_lt","1.0.0-0")
        package_a._register_dependency("a_sub_b","version_lt","1.0.0-0")
        package_a._register_dependency("a_sub_c","version_lt","1.0.0-0")

        dep_manager.register_package(package_a)
        dep_manager.calculate_installs()

        package_ab = MockPackage("a_sub_b","0.0.1-9")
        package_ab._register_dependency("ab_sub_a","version_gt","1.0.0-0")
        package_ab._register_dependency("ab_sub_b","version_gt","1.0.0-0")
        package_ab._register_dependency("ab_sub_c","version_gte","1.0.0-0")

        dep_manager.register_package(package_ab)
        dep_manager.calculate_installs()

        package_abb = MockPackage("ab_sub_b")
        package_abb._register_dependency("abb_sub_a","version_gt","1.0.0-0")
        package_abb._register_dependency("abb_sub_b","version_gt","1.0.0-0")
        package_abb._register_dependency("abb_sub_c","version_gte","1.0.0-0")

        dep_manager.register_package(package_abb)
        dep_manager.calculate_installs()

        dep_manager.render_tree(True)
        self.assertNotIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

        for candidate in dep_manager.get_install_list():
            if candidate["name"] == "ab_sub_b":
                self.assertEqual(candidate["version"], "2.0.0-8")

        # trest if subnode of the going_to_be_replaced tree is ignored like expected
        package_abb = MockPackage("ab_sub_b_clone")
        package_abb._register_dependency("abb_sub_a","version_gt","1.0.0-1")
        dep_manager.register_package(package_abb)
        dep_manager.render_tree(True)
        self.assertNotIn("abb_sub_a", dep_manager._possible_install_candidate_compromised)


        package_colider = MockPackage("colider")
        package_colider._register_dependency("ab_sub_b","version_lt","2.0.0-0")
        dep_manager.register_package(package_colider)
        self.assertIn("ab_sub_b", dep_manager._possible_install_candidate_compromised)

        dep_manager.calculate_installs()
        for candidate in dep_manager.get_install_list():
                if candidate["name"] == "ab_sub_b":
                    self.assertEqual(candidate["version"], "1.2.0-3")

        # conflicting node is kept
        self.assertIn({'operator': 'version_gt', 'version': '1.0.0-0', 'from': 'a_sub_b=0.0.1-9'}, dep_manager._dependency_bank["ab_sub_b"])
        self.assertIn({'operator': 'version_lt', 'version': '2.0.0-0', 'from': 'colider=0.0.0.0'}, dep_manager._dependency_bank["ab_sub_b"])

        # trest if subnode of the going_to_be_replaced tree is taken in considerelf.assertIn({'operator': 'version_gt', 'version': '1.0.0-0', 'from': 'a_sub_b'}, dep_manager._dependency_bank["ab_sub_b"])ation now
        package_abb = MockPackage("ab_sub_b_clone2")
        package_abb._register_dependency("abb_sub_a","version_gt","1.0.0-2")
        dep_manager.register_package(package_abb)
        dep_manager.render_tree(True)
        self.assertIn("abb_sub_a", dep_manager._possible_install_candidate_compromised)

        # no traces of tree lower than the conflict. needs to be rebuilt with the new candidate
        self.assertNotIn({'operator': 'version_gt', 'version': '1.0.0-0', 'from': 'ab_sub_b=0.0.0.0'}, dep_manager._dependency_bank["abb_sub_a"])
        self.assertNotIn({'operator': 'version_gt', 'version': '1.0.0-0', 'from': 'ab_sub_b=0.0.0.0'}, dep_manager._dependency_bank["abb_sub_b"])
        self.assertNotIn({'operator': 'version_gte', 'version': '1.0.0-0', 'from': 'ab_sub_b=0.0.0.0'}, dep_manager._dependency_bank["abb_sub_c"])

