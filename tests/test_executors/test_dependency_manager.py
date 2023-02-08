from mobros.ros_install_build_deps.dependency_manager import DependencyManager, find_highest_bottom_rule, find_lowest_top_rule, find_equals_rule, find_candidate_online
from mobros.ros_install_build_deps.catkin_package_manager import CatkinPackage
import os
import unittest
import mock

def load_test_resource_workspace(WORKSPACE_NAME):
  dep_manager= DependencyManager()
  TEST_RESOURCE_PATH_VALID=os.path.join(os.getcwd(),"tests","resources","test_dependencies",WORKSPACE_NAME)
  for path, subdirs, files in os.walk(TEST_RESOURCE_PATH_VALID):
    for name in files:
      if name == "package.xml":
          package = CatkinPackage(os.path.join(path, name))
          dep_manager.register_package(package)
  
  return dep_manager

DUMMY_AVAIABLE_VERSIONS=['2.0.0-8', '2.0.0-7', '2.0.0-6', '2.0.0-5', '2.0.0-4', '2.0.0-3', 
                         '1.2.0-3', '1.2.0-2', '1.2.0-1', '1.1.0-3', '1.1.0-2', '1.1.0-1', 
                         '1.0.2-21', '1.0.2-20', '1.0.2-19', '1.0.2-18', '1.0.2-17', '1.0.2-16',
                         '1.0.2-15', '1.0.2-14', '1.0.2-13', '1.0.2-12', '1.0.2-11', '1.0.2-10', 
                         '1.0.2-9', '1.0.2-8', '1.0.2-7', '1.0.2-6', '1.0.2-5', '1.0.2-4', '1.0.2-3', 
                         '1.0.2-2', '1.0.2-1', '1.0.1-4', '1.0.1-3', '1.0.1-2', '1.0.1-1', '1.0.0-100',
                         '1.0.0-99', '1.0.0-98', '1.0.0-97', '1.0.0-96', '1.0.0-95', '1.0.0-94', '1.0.0-93',
                         '1.0.0-92', '1.0.0-91', '1.0.0-90', '1.0.0-89', '1.0.0-88', '1.0.0-87', '1.0.0-86',
                         '1.0.0-85', '1.0.0-84', '1.0.0-83', '1.0.0-82', '1.0.0-81', '1.0.0-80', '1.0.0-79',
                         '1.0.0-78', '1.0.0-77', '1.0.0-76', '1.0.0-75', '1.0.0-74', '1.0.0-73', '1.0.0-72',
                         '1.0.0-71', '1.0.0-70', '1.0.0-69', '1.0.0-68', '1.0.0-67', '1.0.0-66', '1.0.0-65',
                         '1.0.0-64', '1.0.0-63', '1.0.0-62', '1.0.0-61', '1.0.0-60', '1.0.0-59', '1.0.0-58',
                         '1.0.0-57', '1.0.0-56', '1.0.0-55', '1.0.0-54', '1.0.0-53', '1.0.0-52', '1.0.0-51',
                         '1.0.0-50', '1.0.0-49', '1.0.0-48', '1.0.0-47', '1.0.0-46', '1.0.0-45', '1.0.0-44',
                         '1.0.0-43', '1.0.0-42', '1.0.0-41', '1.0.0-40', '1.0.0-39', '1.0.0-38', '1.0.0-37',
                         '1.0.0-36', '1.0.0-35', '1.0.0-34', '1.0.0-33', '1.0.0-32', '1.0.0-31', '1.0.0-30',
                         '1.0.0-29', '1.0.0-28', '1.0.0-27', '1.0.0-26', '1.0.0-25', '1.0.0-24', '1.0.0-23',
                         '1.0.0-22', '1.0.0-21', '1.0.0-20', '1.0.0-19', '1.0.0-18', '1.0.0-17', '1.0.0-16',
                         '1.0.0-15', '1.0.0-14', '1.0.0-13', '1.0.0-12', '1.0.0-11', '1.0.0-10', '1.0.0-9',
                         '1.0.0-8', '1.0.0-7', '1.0.0-6', '1.0.0-5', '1.0.0-4', '1.0.0-3', '1.0.0-2', '0.0.1-11',
                         '0.0.1-8', '0.0.1-7', '0.0.1-6', '0.0.1-5', '0.0.1-4', '0.0.1-3', '0.0.1-2', '0.0.1-1',
                         '0.0.0-8', '0.0.0-7', '0.0.0-6', '0.0.0-5', '0.0.0-4', '0.0.0-3', '0.0.0-2']


class TestDependencyManager(unittest.TestCase):

    def test_register_package(self):
        dep_manager= load_test_resource_workspace("tree_simple_valid_deps")
                
        dependency=dep_manager._dependency_bank["ompl"][0]
        self.assertEqual(dependency["from"], "package_a")
        self.assertEqual(dependency["operator"], "version_lte")
        self.assertEqual(dependency["version"], "1.5.2-6")

    def test_exclude_package(self):
      dep_manager= DependencyManager()
      TEST_KEY="test"
      TEST_EXCLUDED_KEY="test_exclude"
      dep_manager._dependency_bank[TEST_KEY]=[]
      dep_manager._dependency_bank[TEST_EXCLUDED_KEY]=[]
      self.assertEqual(dep_manager._dependency_bank[TEST_EXCLUDED_KEY], [])
      dep_manager.exclude_package(TEST_EXCLUDED_KEY)
      self.assertFalse(TEST_EXCLUDED_KEY in dep_manager._dependency_bank)
      self.assertEqual(dep_manager._dependency_bank[TEST_KEY], [])
      
    def test_conflict_detection_edges_clash(self):
      dep_manager = load_test_resource_workspace("tree_conflict_edges")
      
      with self.assertRaises(SystemExit) as method_execution_exit:
        dep_manager.check_colisions()

      self.assertEqual(method_execution_exit.exception.code, 1)

    def test_conflict_detection_multi_equals_clash(self):
      dep_manager = load_test_resource_workspace("tree_conflict_equals_clash")
      
      with self.assertRaises(SystemExit) as method_execution_exit:
        dep_manager.check_colisions()

      self.assertEqual(method_execution_exit.exception.code, 1)


    def test_conflict_detection_equals_top_clash(self):
      dep_manager = load_test_resource_workspace("tree_conflict_equals_top")
      
      with self.assertRaises(SystemExit) as method_execution_exit:
        dep_manager.check_colisions()

      self.assertEqual(method_execution_exit.exception.code, 1)
      
    def test_conflict_detection_equals_bottom_clash(self):
      dep_manager = load_test_resource_workspace("tree_conflict_equals_bottom")
      
      with self.assertRaises(SystemExit) as method_execution_exit:
        dep_manager.check_colisions()

      self.assertEqual(method_execution_exit.exception.code, 1)
    
    def test_conflict_valid_bottom_inclusion(self):
      dep_manager = load_test_resource_workspace("tree_valid_bottom_inclusion")
      
      dep_manager.check_colisions()

    def test_conflict_valid_top_inclusion(self):
      dep_manager = load_test_resource_workspace("tree_valid_top_inclusion")
      
      dep_manager.check_colisions()
    
    def test_find_highest_bottom_rule(self):

      version_rules=[]
      version_rules.append({"version":"0.2.0-7000","operator":"version_gte","from":"dummy"})
      version_rules.append({"version":"0.900.0-0","operator":"version_gte","from":"dummy"})
      version_rules.append({"version":"4.0.900-0","operator":"version_gt","from":"dummy"})
      version_rules.append({"version":"0.900.0-0","operator":"version_lte","from":"dummy"})
      version_rules.append({"version":"1.0.0-0","operator":"version_gt","from":"dummy"})
      highest_bottom=find_highest_bottom_rule(version_rules)
      self.assertEqual(highest_bottom["version"],"4.0.900-0")
      self.assertEqual(highest_bottom["included"], False)
      
      version_rules=[]
      version_rules.append({"version":"0.2.0-7000","operator":"version_gte","from":"dummy"})
      version_rules.append({"version":"0.900.0-0","operator":"version_gte","from":"dummy"})
      version_rules.append({"version":"4.0.900-0","operator":"version_gte","from":"dummy"})
      version_rules.append({"version":"0.900.0-0","operator":"version_lte","from":"dummy"})
      version_rules.append({"version":"1.0.0-0","operator":"version_gt","from":"dummy"})
      highest_bottom=find_highest_bottom_rule(version_rules)
      self.assertEqual(highest_bottom["version"],"4.0.900-0")
      self.assertEqual(highest_bottom["included"], True)
      
    def test_find_lowest_top_rule(self):

      version_rules=[]
      version_rules.append({"version":"0.2.0-7000","operator":"version_lte","from":"dummy"})
      version_rules.append({"version":"0.900.0-0","operator":"version_lte","from":"dummy"})
      version_rules.append({"version":"4.0.900-0","operator":"version_lt","from":"dummy"})
      version_rules.append({"version":"4.0.900-0","operator":"version_gt","from":"dummy"})
      version_rules.append({"version":"1.0.0-0","operator":"version_lt","from":"dummy"})
      lowest_top=find_lowest_top_rule(version_rules)
      self.assertEqual(lowest_top["version"],"0.2.0-7000")
      self.assertEqual(lowest_top["included"], True)
      
      version_rules=[]
      version_rules.append({"version":"0.2.0-7000","operator":"version_lt","from":"dummy"})
      version_rules.append({"version":"0.900.0-0","operator":"version_lte","from":"dummy"})
      version_rules.append({"version":"4.0.900-0","operator":"version_lt","from":"dummy"})
      version_rules.append({"version":"4.0.900-0","operator":"version_gt","from":"dummy"})
      version_rules.append({"version":"1.0.0-0","operator":"version_lt","from":"dummy"})
      lowest_top=find_lowest_top_rule(version_rules)
      self.assertEqual(lowest_top["version"],"0.2.0-7000")
      self.assertEqual(lowest_top["included"], False)
      
      
    def test_find_equals_rule(self):

      version_rules=[]
      version_rules.append({"version":"0.2.0-7000","operator":"version_lte","from":"dummy"})
      version_rules.append({"version":"0.900.0-0","operator":"version_lte","from":"dummy"})
      version_rules.append({"version":"4.0.900-0","operator":"version_lt","from":"dummy"})
      version_rules.append({"version":"1.0.0-0","operator":"version_lt","from":"dummy"})
      version_rules.append({"version":"1.0.0-0","operator":"version_eq","from":"dummy"})
      found, equals_rule_found=find_equals_rule(version_rules)
      self.assertTrue(found)
      self.assertEqual(equals_rule_found["version"],"1.0.0-0")

    def test_find_equals_rule_not_found(self):

      version_rules=[]
      version_rules.append({"version":"0.2.0-7000", "operator":"version_lte","from":"dummy"})
      version_rules.append({"version":"0.900.0-0", "operator":"version_lte","from":"dummy"})
      version_rules.append({"version":"4.0.900-0", "operator":"version_lt","from":"dummy"})
      version_rules.append({"version":"1.0.0-0", "operator":"version_lt","from":"dummy"})
      version_rules.append({"version":"1.0.0-0", "operator":"version_gt","from":"dummy"})
      found, equals_rule_found=find_equals_rule(version_rules)
      self.assertFalse(found)
      self.assertIsNone(equals_rule_found)

    @mock.patch("mobros.utils.apt_utils.get_package_avaiable_versions",return_value=[] )
    def test_find_candidate_online_no_online_candidates(self, mock_get_avaiable_versions):
      
      with self.assertRaises(SystemExit) as method_execution_exit:
        find_candidate_online("ros-noetic-mobros",[])

      self.assertEqual(method_execution_exit.exception.code, 1)

    @mock.patch("mobros.utils.apt_utils.get_package_avaiable_versions", return_value = DUMMY_AVAIABLE_VERSIONS)
    def test_find_candidate_online_edges(self, mock_get_avaiable_versions):
      
      version_rules=[]
      version_rules.append({"version":"1.0.0-0", "operator":"version_gt","from":"dummy2"})
      version_rules.append({"version":"2.0.0-0", "operator":"version_lte","from":"dummy"})
      
      version=find_candidate_online("ros-noetic-mobros",version_rules)
      self.assertEqual(version, "1.2.0-3")
      
      
      version_rules=[]
      version_rules.append({"version":"1.0.0-0", "operator":"version_gt","from":"dummy2"})
      version_rules.append({"version":"1.0.2-1", "operator":"version_gte","from":"dummy2"})
      version_rules.append({"version":"2.0.0-3", "operator":"version_lte","from":"dummy"})
      
      version=find_candidate_online("ros-noetic-mobros",version_rules)
      self.assertEqual(version, "2.0.0-3")

    @mock.patch("mobros.utils.apt_utils.get_package_avaiable_versions", return_value = DUMMY_AVAIABLE_VERSIONS)
    def test_find_candidate_online_specific_equals(self, mock_get_avaiable_versions):
      
      version_rules=[]
      version_rules.append({"version":"1.0.0-55", "operator":"version_eq", "from":"dummy"})
      version=find_candidate_online("ros-noetic-mobros",version_rules)
      self.assertEqual(version, "1.0.0-55")
      
      version_rules=[]
      version_rules.append({"version":"2.0.0-3", "operator":"version_eq","from":"dummy"})
      version=find_candidate_online("ros-noetic-mobros",version_rules)
      self.assertEqual(version, "2.0.0-3")
      
      version_rules=[]
      version_rules.append({"version":"0.0.0-5", "operator":"version_eq","from":"dummy"})
      version=find_candidate_online("ros-noetic-mobros",version_rules)
      self.assertEqual(version, "0.0.0-5")