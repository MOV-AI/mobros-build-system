from mobros.ros_install_build_deps.dependency_manager import DependencyManager
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

class TestDependencyManager(unittest.TestCase):

    def test_register_package(
        self
    ):
        dep_manager= load_test_resource_workspace("tree_simple_valid_deps")
                
        dependency=dep_manager._dependency_bank["ompl"][0]
        self.assertEqual(dependency["from"], "package_a")
        self.assertEqual(dependency["operator"], "version_lte")
        self.assertEqual(dependency["version"], "1.5.2-6")

    def test_conflict_detection_edges_clash(self):
      dep_manager = load_test_resource_workspace("tree_conflict_edges")
      
      with self.assertRaises(SystemExit) as cm:
        dep_manager.check_colisions()

      self.assertEqual(cm.exception.code, 1)

    def test_conflict_detection_multi_equals_clash(self):
      dep_manager = load_test_resource_workspace("tree_conflict_equals_clash")
      
      with self.assertRaises(SystemExit) as cm:
        dep_manager.check_colisions()

      self.assertEqual(cm.exception.code, 1)


    def test_conflict_detection_equals_top_clash(self):
      dep_manager = load_test_resource_workspace("tree_conflict_equals_top")
      
      with self.assertRaises(SystemExit) as cm:
        dep_manager.check_colisions()

      self.assertEqual(cm.exception.code, 1)
      
    def test_conflict_detection_equals_bottom_clash(self):
      dep_manager = load_test_resource_workspace("tree_conflict_equals_bottom")
      
      with self.assertRaises(SystemExit) as cm:
        dep_manager.check_colisions()

      self.assertEqual(cm.exception.code, 1)
    
    def test_conflict_valid_bottom_inclusion(self):
      dep_manager = load_test_resource_workspace("tree_valid_bottom_inclusion")
      
      dep_manager.check_colisions()

    def test_conflict_valid_top_inclusion(self):
      dep_manager = load_test_resource_workspace("tree_valid_top_inclusion")
      
      dep_manager.check_colisions()