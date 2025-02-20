""" Module with the ability to interpret a catkin package.xml into a runtime object
"""
import xml.etree.ElementTree as ET
from os.path import isfile, join

import mobros.utils.logger as logging
from mobros.constants import CATKIN_BLACKLIST_FILES
from mobros.utils import utilitary


def is_catkin_blacklisted(path):
    """ Function that checks if a given path contains a catkin blacklist file

    Args:
        path (os.path): OS path

    Returns:
        bool: result of the evaluation if there are blacklist files in the given path
    """
    for black_list_file in CATKIN_BLACKLIST_FILES:
        if isfile(join(path, black_list_file)):
            return True
    return False


class CatkinPackage:
    """ Class that represents a catkin package and its dependencies"""

    def __init__(self, package_path, workspace_pkg_list=None):

        if workspace_pkg_list is None:
            workspace_pkg_list = []

        self.build_dependencies = {}

        tree = ET.parse(package_path)
        root = tree.getroot()
        self.package_name = root.findall("name")[0].text

        self._find_dependencies("build_depend", self.build_dependencies, root, workspace_pkg_list)
        self._find_dependencies("depend", self.build_dependencies, root, workspace_pkg_list)
        self._find_dependencies("test_depend", self.build_dependencies, root, workspace_pkg_list)

    @staticmethod
    def extract_name(package_path):
        """method to extract the package name from the package.xml file

        Args:
            package_path (str): Path to the package.xml file

        Returns:
            str: Catkin package name
        """
        tree = ET.parse(package_path)
        root = tree.getroot()
        return root.findall("name")[0].text

    def get_dependencies(self):
        """Getter function to retrieve the package dependencies. Both depend and build_depend elements.

        Returns:
            list: list of dependencies of the catkin package.
        """
        return self.build_dependencies

    def get_name(self):
        """Getter function to retrieve the package name

        Returns:
           str: catkin package name
        """
        return self.package_name

    def _find_dependencies(self, dependency_type, dependency_object, xml_root, blacklist):
        """Function that finds the dependencies of a catkin package by type (depend or build_depend)

        Args:
            dependency_type (str): Either 'depend' or 'build_depend' element type
            dependency_object (xml_obj): xml dependency element
            xml_root (xml_obj): package xml root element
        """
        for child in xml_root.findall(dependency_type):
            dependency_name = (child.text).strip()
            if dependency_name in blacklist:
                continue

            deb_names = utilitary.translate_package_name(dependency_name)

            for deb_name in deb_names:

                logging.debug(
                    "[Dependency_Manager - check_colisions] Dependency: "
                    + dependency_name
                    + " has been translated to "
                    + deb_name
                )

                if deb_name not in dependency_object:
                    dependency_object[deb_name] = []

                if child.attrib:
                    for key in child.attrib:
                        dependency_operator = key
                        dependency_version = child.attrib[key]

                        dependency_object[deb_name].append(
                            {
                                "operator": dependency_operator,
                                "version": dependency_version,
                                "from": self.package_name,
                            }
                        )
                else:
                    dependency_object[deb_name].append(
                        {
                            "operator": "",
                            "version": None,
                            "from": self.package_name,
                        }
                    )
