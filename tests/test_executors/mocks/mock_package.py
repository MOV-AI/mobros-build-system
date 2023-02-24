
""" Module with the ability to interpret a catkin package.xml into a runtime object
"""
import xml.etree.ElementTree as ET
from os.path import isfile, join

from mobros.constants import CATKIN_BLACKLIST_FILES
from mobros.types.intternal_package import PackageInterface
from mobros.utils import utilitary
import  mobros.utils.logger as logging


class MockPackage():
    """Class that serializes from xml to object a catkin xml package file"""

    def __init__(self, package_name, version="0.0.0.0"):
        self.dependencies = {}

        self.package_name = package_name
        self.version = version

    def get_dependencies(self):
        """Getter function to retrieve the package dependencies. Both depend and build_depend elements.

        Returns:
            list: list of dependencies of the catkin package.
        """
        return self.dependencies

    def get_name(self):
        """Getter function to retrieve the package name

        Returns:
           str: catkin package name
        """
        return self.package_name

    def _find_dependencies(self):
        """_summary_

        Args:
            dependency_type (str): Either 'depend' or 'build_depend' element type
            dependency_object (xml_obj): xml dependency element
            xml_root (xml_obj): package xml root element
        """
        return

    def _register_dependency(self, dep_name, relation, version):
        
        if dep_name not in self.dependencies:
            self.dependencies[dep_name] = []     

        self.dependencies[dep_name].append(
            {
                "operator": relation,
                "version": version,
                "from": self.package_name + "=" + self.version
            }
        )
