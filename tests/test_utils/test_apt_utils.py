
import unittest
import mock
from mobros.types.apt_cache_singleton import AptCache
from mobros.types.mobros_global_data import GlobalData
from tests.test_executers.mocks.mock_apt_cache import MockAptInstalledCache,MockPkgDependency, MockAptCache, MockAptVersion
from tests.test_executers.mocks.mock_local_deb_package import DebPackage
from mobros.utils import apt_utils 
from mobros.utils.version_utils import create_version_rule
from mobros.constants import OPERATION_TRANSLATION_TABLE

INSTALLED_PKG_DEPENDENCIES_PY_1_0 = [MockPkgDependency("python3","=","1.0.0-0")]
PKG_NAME= "my_app"
PKG_VERSION = "0.0.0-1"

INSTALLED_PKG_DEPENDENCIES_PY_GT_1_0 = [MockPkgDependency("python3",">","1.0.0-0")]
INSTALLED_PKG_DEPENDENCIES_PY_GTE_1_1 = [MockPkgDependency("python3",">=","1.1.0-0")]
INSTALLED_PKG_DEPENDENCIES_PY_LT_1_0 = [MockPkgDependency("python3","<","1.0.0-0")]
INSTALLED_PKG_DEPENDENCIES_PY_LTE_0_9 = [MockPkgDependency("python3","<=","0.9.0-0")]

class TestAptUtilsPackageImpactsInstalled(unittest.TestCase):

    @mock.patch("mobros.types.apt_cache_singleton.AptCache.__new__", return_value=MockAptInstalledCache(PKG_NAME, PKG_VERSION, [INSTALLED_PKG_DEPENDENCIES_PY_1_0]))
    def test_package_impacts_installed_conflict(self, mock_apt_cache_new):
        impacted = apt_utils.package_impacts_installed_dependencies(["python3", {"version": "2.0.0-0"}])
        self.assertIsNotNone(impacted)
        print(impacted)

        TRANSLATED_OPERATION = OPERATION_TRANSLATION_TABLE[INSTALLED_PKG_DEPENDENCIES_PY_1_0[0].relation]
        DEPENDENCY_INFO = {'name': INSTALLED_PKG_DEPENDENCIES_PY_1_0[0].name, 'version': INSTALLED_PKG_DEPENDENCIES_PY_1_0[0].version, 'operation': TRANSLATED_OPERATION}
        EXPECTED_RESULT = {'name': PKG_NAME, 'version': PKG_VERSION, 'dependency': DEPENDENCY_INFO}
        self.assertEqual(impacted, EXPECTED_RESULT)

    @mock.patch("mobros.types.apt_cache_singleton.AptCache.__new__", return_value=MockAptInstalledCache(PKG_NAME, PKG_VERSION, [INSTALLED_PKG_DEPENDENCIES_PY_1_0]))
    def test_package_impacts_installed_no_conflict(self, mock_apt_cache_new):
        impacted = apt_utils.package_impacts_installed_dependencies(["python3", {"version": "1.0.0-0"}])
        self.assertIsNone(impacted)

    @mock.patch("mobros.types.apt_cache_singleton.AptCache.__new__", return_value=MockAptInstalledCache(PKG_NAME, PKG_VERSION, [INSTALLED_PKG_DEPENDENCIES_PY_LT_1_0]))
    def test_package_impacts_installed_no_conflict_lt(self, mock_apt_cache_new):
        impacted = apt_utils.package_impacts_installed_dependencies(["python3", {"version": "0.9.0-0"}])
        self.assertIsNone(impacted)

    @mock.patch("mobros.types.apt_cache_singleton.AptCache.__new__", return_value=MockAptInstalledCache(PKG_NAME, PKG_VERSION, [INSTALLED_PKG_DEPENDENCIES_PY_LTE_0_9]))
    def test_package_impacts_installed_no_conflict_lte(self, mock_apt_cache_new):
        impacted = apt_utils.package_impacts_installed_dependencies(["python3", {"version": "0.9.0-0"}])
        self.assertIsNone(impacted)

    @mock.patch("mobros.types.apt_cache_singleton.AptCache.__new__", return_value=MockAptInstalledCache(PKG_NAME, PKG_VERSION, [INSTALLED_PKG_DEPENDENCIES_PY_GT_1_0]))
    def test_package_impacts_installed_conclict_gt(self, mock_apt_cache_new):
        impacted = apt_utils.package_impacts_installed_dependencies(["python3", {"version": "1.0.0-0"}])
        self.assertIsNotNone(impacted)
        print(impacted)
        
        TRANSLATED_OPERATION = OPERATION_TRANSLATION_TABLE[INSTALLED_PKG_DEPENDENCIES_PY_GT_1_0[0].relation]
        DEPENDENCY_INFO = {'name': INSTALLED_PKG_DEPENDENCIES_PY_GT_1_0[0].name, 'version': INSTALLED_PKG_DEPENDENCIES_PY_GT_1_0[0].version, 'operation': TRANSLATED_OPERATION}
        EXPECTED_RESULT = {'name': PKG_NAME, 'version': PKG_VERSION, 'dependency': DEPENDENCY_INFO}
        self.assertEqual(impacted, EXPECTED_RESULT)
        
    @mock.patch("mobros.types.apt_cache_singleton.AptCache.__new__", return_value=MockAptInstalledCache(PKG_NAME, PKG_VERSION, [INSTALLED_PKG_DEPENDENCIES_PY_GTE_1_1]))
    def test_package_impacts_installed_conclict_gte(self, mock_apt_cache_new):

        impacted = apt_utils.package_impacts_installed_dependencies(["python3", {"version": "1.0.0-0"}])
        self.assertIsNotNone(impacted)
        print(impacted)
        
        TRANSLATED_OPERATION = OPERATION_TRANSLATION_TABLE[INSTALLED_PKG_DEPENDENCIES_PY_GTE_1_1[0].relation]
        DEPENDENCY_INFO = {'name': INSTALLED_PKG_DEPENDENCIES_PY_GTE_1_1[0].name, 'version': INSTALLED_PKG_DEPENDENCIES_PY_GTE_1_1[0].version, 'operation': TRANSLATED_OPERATION}
        EXPECTED_RESULT = {'name': PKG_NAME, 'version': PKG_VERSION, 'dependency': DEPENDENCY_INFO}
        self.assertEqual(impacted, EXPECTED_RESULT)
        
    @mock.patch("mobros.types.apt_cache_singleton.AptCache.__new__", return_value=MockAptInstalledCache(PKG_NAME, PKG_VERSION, [INSTALLED_PKG_DEPENDENCIES_PY_LT_1_0]))
    def test_package_impacts_installed_conclict_lt(self, mock_apt_cache_new):

        impacted = apt_utils.package_impacts_installed_dependencies(["python3", {"version": "1.0.0-0"}])
        self.assertIsNotNone(impacted)
        print(impacted)
        
        TRANSLATED_OPERATION = OPERATION_TRANSLATION_TABLE[INSTALLED_PKG_DEPENDENCIES_PY_LT_1_0[0].relation]
        DEPENDENCY_INFO = {'name': INSTALLED_PKG_DEPENDENCIES_PY_LT_1_0[0].name, 'version': INSTALLED_PKG_DEPENDENCIES_PY_LT_1_0[0].version, 'operation': TRANSLATED_OPERATION}
        EXPECTED_RESULT = {'name': PKG_NAME, 'version': PKG_VERSION, 'dependency': DEPENDENCY_INFO}
        self.assertEqual(impacted, EXPECTED_RESULT)

    @mock.patch("mobros.types.apt_cache_singleton.AptCache.__new__", return_value=MockAptInstalledCache(PKG_NAME, PKG_VERSION, [INSTALLED_PKG_DEPENDENCIES_PY_LTE_0_9]))
    def test_package_impacts_installed_conclict_lte(self, mock_apt_cache_new):

        impacted = apt_utils.package_impacts_installed_dependencies(["python3", {"version": "1.0.0-0"}])
        self.assertIsNotNone(impacted)
        print(impacted)
        
        TRANSLATED_OPERATION = OPERATION_TRANSLATION_TABLE[INSTALLED_PKG_DEPENDENCIES_PY_LTE_0_9[0].relation]
        DEPENDENCY_INFO = {'name': INSTALLED_PKG_DEPENDENCIES_PY_LTE_0_9[0].name, 'version': INSTALLED_PKG_DEPENDENCIES_PY_LTE_0_9[0].version, 'operation': TRANSLATED_OPERATION}
        EXPECTED_RESULT = {'name': PKG_NAME, 'version': PKG_VERSION, 'dependency': DEPENDENCY_INFO}
        self.assertEqual(impacted, EXPECTED_RESULT)

mock_apt_versions = []
mock_apt_versions.append(MockAptVersion("0.0.0-1", [[MockPkgDependency("python3","","0.1.0-0")], [MockPkgDependency("python2","","1.5.0-0")]]))
mock_apt_versions.append(MockAptVersion("0.0.0-2", [[MockPkgDependency("python3","","2.0.0-0")], [MockPkgDependency("python2","","0.0.0-1")]]))

class TestAptUtilsFindCandidateFullfillingDependency(unittest.TestCase):

    @mock.patch("mobros.types.apt_cache_singleton.AptCache.__new__", return_value=MockAptCache(mock_apt_versions))
    def test_fullfill_dependency_single_candidate(self, mock_apt_cache_new):

        candidates = apt_utils.find_candidates_online_fullfilling_dependency(PKG_NAME, "python3", create_version_rule(OPERATION_TRANSLATION_TABLE[">"], "1.0.0-0", ""))
        self.assertEqual(len(candidates), 1)
        
        self.assertListEqual(["0.0.0-2"], candidates)

    @mock.patch("mobros.types.apt_cache_singleton.AptCache.__new__", return_value=MockAptCache(mock_apt_versions))
    def test_fullfill_dependency_multi_candidate(self, mock_apt_cache_new):

        candidates = apt_utils.find_candidates_online_fullfilling_dependency(PKG_NAME, "python3", create_version_rule(OPERATION_TRANSLATION_TABLE[">"], "0.0.1-0", ""))
        self.assertEqual(len(candidates), 2)
        
        self.assertListEqual(["0.0.0-1", "0.0.0-2"], candidates)

    @mock.patch("mobros.types.apt_cache_singleton.AptCache.__new__", return_value=MockAptCache(mock_apt_versions))
    def test_fullfill_dependency_any(self, mock_apt_cache_new):

        candidates = apt_utils.find_candidates_online_fullfilling_dependency(PKG_NAME, "python3", create_version_rule(OPERATION_TRANSLATION_TABLE[""], "0.0.1-0", ""))
        self.assertEqual(len(candidates), len(mock_apt_versions))
        
        self.assertListEqual(["0.0.0-1", "0.0.0-2"], candidates)
        

    @mock.patch("mobros.types.apt_cache_singleton.AptCache.__new__", return_value=MockAptCache(mock_apt_versions))
    def test_fullfill_dependency_no_candidate(self, mock_apt_cache_new):

        candidates = apt_utils.find_candidates_online_fullfilling_dependency(PKG_NAME, "python3", create_version_rule(OPERATION_TRANSLATION_TABLE["="], "0.0.1-0", ""))
        self.assertEqual(len(candidates), 0)

g_data = GlobalData()
g_data.set_user_package("ros-movai","0.1.2-3")

class TestAptUtils(unittest.TestCase):
    def test_clean_apt_versions(self):
        package_version_list = ["pkg_a=0.0.0-1", "pkg_b=0.0.0-2", "pkg_c=0.0.0-3"]
        clean_version_list = apt_utils.clean_apt_versions(package_version_list)
        self.assertListEqual(clean_version_list, ["0.0.0-3","0.0.0-2","0.0.0-1"])
    
    def test_apt_install_package(self):
        apt_utils.install_package("banana","0.0.0", True)
        
    @mock.patch("mobros.types.apt_cache_singleton.AptCache.__new__", return_value=MockAptInstalledCache(PKG_NAME, PKG_VERSION, [INSTALLED_PKG_DEPENDENCIES_PY_1_0]))
    def test_cache_package_origin(self, mock_apt_cache_new):
        apt_utils.get_package_origin("python3")
    
    @mock.patch("mobros.types.apt_cache_singleton.AptCache.__new__", return_value=MockAptCache(mock_apt_versions))
    def test_get_package_available_versions(self, mock_apt_cache_new):
        clean_version_list = apt_utils.get_package_available_versions("python2")
        self.assertListEqual(clean_version_list, ["0.0.0-2","0.0.0-1"])
    
    @mock.patch("mobros.types.apt_cache_singleton.AptCache.__new__", return_value=MockAptInstalledCache(PKG_NAME, PKG_VERSION, [INSTALLED_PKG_DEPENDENCIES_PY_1_0]))
    def test_get_package_installed_version(self, mock_apt_cache_new):
        version= apt_utils.get_package_installed_version("python2")
        self.assertEqual(version, PKG_VERSION)
    
    def test_is_package_local_file(self):
        self.assertTrue(apt_utils.is_package_local_file("./ros.deb"))
        self.assertTrue(apt_utils.is_package_local_file("/opt/noetic/ros.deb"))
        self.assertFalse(apt_utils.is_package_local_file("/opt/noetic/ros.tar"))
        self.assertFalse(apt_utils.is_package_local_file("ros-noetic-movai-ros"))

    @mock.patch("mobros.types.apt_cache_singleton.AptCache.__new__", return_value=MockAptInstalledCache(PKG_NAME, PKG_VERSION, [INSTALLED_PKG_DEPENDENCIES_PY_1_0]))
    def test_is_package_already_installed(self, mock_apt_cache_new):
        self.assertTrue(apt_utils.is_package_already_installed("python2"))
        self.assertFalse(apt_utils.is_package_already_installed("python2", "0.0.1-1"))
        self.assertTrue(apt_utils.is_package_already_installed("python2",PKG_VERSION))
    
    @mock.patch("apt.debfile.DebPackage.__new__", return_value= DebPackage("ros-noetic-ros", "1.1.1-1"))
    def test_get_local_deb_info(self, mock_deb_Package_new):
        deb_name, deb_version, dependencies = apt_utils.get_local_deb_info("/opt/ros/noetic/ros.deb")
        self.assertEqual(deb_name, "ros-noetic-ros")
        self.assertEqual(deb_version, "1.1.1-1")
        
    @mock.patch("apt.debfile.DebPackage.__new__", return_value= DebPackage("ros-noetic-ros", "1.1.1-1"))
    def test_get_local_deb_name_version_not_found(self, mock_deb_Package_new):
        
        with self.assertRaises(SystemExit) as method_execution_exit:
            apt_utils.get_local_deb_name_version("/opt/ros/noetic/ros.deb")

        self.assertEqual(method_execution_exit.exception.code, 1)
        
    @mock.patch("apt.debfile.DebPackage.__new__", return_value= DebPackage("ros-noetic-ros", "1.1.1-1"))
    def test_get_local_deb_name_version_not_found(self, mock_deb_Package_new):
        
        with self.assertRaises(SystemExit) as method_execution_exit:
            apt_utils.get_local_deb_name_version("/opt/ros/noetic/ros.deb")

        self.assertEqual(method_execution_exit.exception.code, 1)
    
    @mock.patch("os.path.isfile", return_value= True)
    @mock.patch("apt.debfile.DebPackage.__new__", return_value= DebPackage("ros-noetic-ros", "1.1.1-0"))
    def test_get_local_deb_name_version(self, mock_isfile,mock_deb_Package_new):
        
        deb_name, deb_version = apt_utils.get_local_deb_name_version("/opt/ros/noetic/ros.deb")
        self.assertEqual(deb_name, "ros-noetic-ros")
        self.assertEqual(deb_version, "1.1.1-0")
        
    @mock.patch("mobros.utils.apt_utils.dependency_has_candidate", return_value = True)
    @mock.patch("mobros.utils.apt_utils.get_providing_packages", return_value = [MockPkgDependency("sub_virtual1","", "",10),MockPkgDependency("sub_virtual2","", "",80)]) 
    @mock.patch("mobros.utils.apt_utils.is_virtual_package", return_value = True)
    @mock.patch("apt.debfile.DebPackage.__new__", return_value= DebPackage("ros-noetic-ros", "1.1.1-0"))
    def test_check_from_virtual_a_solution_id_sort1(self, mock_deb_Package_new, mock_is_virtual, mock_get_prodividng_packages, mock_has_candidate):
        dependency = MockPkgDependency("virtual_ros", "", "")
        result = apt_utils.check_from_virtual_a_solution([dependency])
        self.assertEqual(result.name, "sub_virtual2")
        
    @mock.patch("mobros.utils.apt_utils.dependency_has_candidate", return_value = True)
    @mock.patch("mobros.utils.apt_utils.get_providing_packages", return_value = [MockPkgDependency("sub_virtual1","", "",100),MockPkgDependency("sub_virtual2","", "",80)]) 
    @mock.patch("mobros.utils.apt_utils.is_virtual_package", return_value = True)
    @mock.patch("apt.debfile.DebPackage.__new__", return_value= DebPackage("ros-noetic-ros", "1.1.1-0"))
    def test_check_from_virtual_a_solution_id_sort2(self, mock_deb_Package_new, mock_is_virtual, mock_get_prodividng_packages, mock_has_candidate):
        dependency = MockPkgDependency("virtual_ros", "", "")
        result = apt_utils.check_from_virtual_a_solution([dependency])
        self.assertEqual(result.name, "sub_virtual1")

    @mock.patch("mobros.types.mobros_global_data.GlobalData.__new__", return_value= GlobalData())
    @mock.patch("mobros.utils.apt_utils.dependency_has_candidate", return_value = True)
    @mock.patch("mobros.utils.apt_utils.get_providing_packages", return_value = [MockPkgDependency("sub_virtual1","", "",100),MockPkgDependency("ros-movai","", "",80)]) 
    @mock.patch("mobros.utils.apt_utils.is_virtual_package", return_value = True)
    @mock.patch("apt.debfile.DebPackage.__new__", return_value= DebPackage("ros-noetic-ros", "1.1.1-0"))
    def test_check_from_virtual_a_solution_user_input(self, mock_deb_Package_new, mock_is_virtual, mock_get_prodividng_packages, mock_has_candidate, mock_global_data):
        dependency = MockPkgDependency("virtual_ros", "", "")
        result = apt_utils.check_from_virtual_a_solution([dependency])
        self.assertEqual(result.name, "ros-movai")
