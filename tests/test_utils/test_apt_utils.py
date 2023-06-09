
import unittest
import mock

from tests.test_executers.mocks.mock_apt_cache import MockAptCache,MockAptPkg,MockPkgDependency
from mobros.utils.apt_utils import (package_impacts_installed_dependencies,
                                    find_candidates_online_fullfilling_dependency)
from mobros.constants import OPERATION_TRANSLATION_TABLE

INSTALLED_PKG_DEPENDENCIES_PY_1_0 = [MockPkgDependency("python3","=","1.0.0-0")]
PKG_NAME= "my_app"
PKG_VERSION = "0.0.0-1"
class TestAptUtils(unittest.TestCase):
    

    @mock.patch("mobros.types.apt_cache_singleton.AptCache.__new__", return_value=MockAptCache(PKG_NAME, PKG_VERSION, [INSTALLED_PKG_DEPENDENCIES_PY_1_0]))
    def test_package_impacts_installed_conflict(self, mock_apt_cache_new):
        result = package_impacts_installed_dependencies(["python3", {"version": "2.0.0-0"}])
        self.assertIsNotNone(result)
        print(result)
        
        TRANSLATED_OPERATION = OPERATION_TRANSLATION_TABLE[INSTALLED_PKG_DEPENDENCIES_PY_1_0[0].relation]
        DEPENDENCY_INFO = {'name': INSTALLED_PKG_DEPENDENCIES_PY_1_0[0].name, 'version': INSTALLED_PKG_DEPENDENCIES_PY_1_0[0].version, 'operation': TRANSLATED_OPERATION}
        EXPECTED_RESULT = {'name': PKG_NAME, 'version': PKG_VERSION, 'dependency': DEPENDENCY_INFO}
        self.assertEqual(result, EXPECTED_RESULT)

    @mock.patch("mobros.types.apt_cache_singleton.AptCache.__new__", return_value=MockAptCache(PKG_NAME, PKG_VERSION, [INSTALLED_PKG_DEPENDENCIES_PY_1_0]))
    def test_package_impacts_installed_no_conflict(self, mock_apt_cache_new):
        result = package_impacts_installed_dependencies(["python3", {"version": "1.0.0-0"}])
        self.assertIsNone(result)
