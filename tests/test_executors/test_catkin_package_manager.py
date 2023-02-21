import os
import unittest
import mock
from mobros.ros_install_build_deps.catkin_package import CatkinPackage
mock_rosdep_translate_map = {
    "ompl": "ros-noetic-ompl",
    "movai_navigation": "ros-noetic-movai-navigation",
}

def mock_translation(key):
    return mock_rosdep_translate_map[key]

class TestCatkinPackageManager(unittest.TestCase):
    @mock.patch("mobros.utils.utilitary.translate_package_name",side_effect=mock_translation)
    def test_package_attributes(self, mock):
        TEST_RESOURCE_PATH_VALID = os.path.join(
            os.getcwd(),
            "tests",
            "resources",
            "test_dependencies",
            "tree_simple_valid_deps",
        )

        PACKAGE_B = os.path.join(TEST_RESOURCE_PATH_VALID, "project_b", "package.xml")
        PACKAGE_A = os.path.join(TEST_RESOURCE_PATH_VALID, "project_a", "package.xml")
        PACKAGE_C = os.path.join(
            TEST_RESOURCE_PATH_VALID,
            "project_a",
            "inner_project",
            "project_c",
            "package.xml",
        )

        package_a = CatkinPackage(PACKAGE_A)
        package_b = CatkinPackage(PACKAGE_B)
        package_c = CatkinPackage(PACKAGE_C)

        self.assertEqual(package_b.get_name(), "package_b")
        self.assertEqual(package_b.get_dependencies(), {})

        self.assertEqual(package_a.get_name(), "package_a")
        self.assertTrue("ros-noetic-ompl" in package_a.get_dependencies())
        self.assertEqual(
            package_a.get_dependencies()["ros-noetic-ompl"][0]["operator"], "version_lte"
        )
        self.assertEqual(package_a.get_dependencies()["ros-noetic-ompl"][0]["version"], "1.5.2-6")
        self.assertEqual(
            package_a.get_dependencies()["ros-noetic-ompl"][1]["operator"], "version_gte"
        )
        self.assertEqual(package_a.get_dependencies()["ros-noetic-ompl"][1]["version"], "0.0.1-23")
        
        self.assertEqual(package_c.get_name(), "package_c")
        self.assertEqual(package_c.get_dependencies()["ros-noetic-movai-navigation"][0]["version"], None)
        self.assertEqual(package_c.get_dependencies()["ros-noetic-movai-navigation"][0]["operator"], "")
        