""" Module with the ability to interpret a catkin package.xml into a runtime object
"""
import xml.etree.ElementTree as ET
from os.path import isfile, join

from mobros.constants import CATKIN_BLACKLIST_FILES


def is_catkin_blacklisted(path):
    """Function that verifies if there are blacklist files in the given path.

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
    """Class that serializes from xml to object a catkin xml package file"""

    def __init__(self, package_path):
        self.build_dependencies = {}

        tree = ET.parse(package_path)
        root = tree.getroot()
        self.package_name = root.findall("name")[0].text

        self._find_dependencies("build_depend", self.build_dependencies, root)
        self._find_dependencies("depend", self.build_dependencies, root)

    def get_build_deps(self):
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

    def _find_dependencies(self, dependency_type, dependency_object, xml_root):
        """_summary_

        Args:
            dependency_type (str): Either 'depend' or 'build_depend' element type
            dependency_object (xml_obj): xml dependency element
            xml_root (xml_obj): package xml root element
        """
        for child in xml_root.findall(dependency_type):
            dependency_name = (child.text).strip()

            if dependency_name not in dependency_object:
                dependency_object[dependency_name] = []
            if child.attrib:
                for key in child.attrib:
                    dependency_operator = key
                    dependency_version = child.attrib[key]

                    dependency_object[dependency_name].append(
                        {
                            "operator": dependency_operator,
                            "version": dependency_version,
                            "from": self.package_name,
                        }
                    )
