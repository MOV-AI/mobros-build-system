from mobros.utils import apt_utils
from mobros.constants import OPERATION_TRANSLATION_TABLE
import time
import mobros.utils.logger as logging

class DebianPackage():
    """Class that serializes from xml to object a catkin xml package file"""

    def __init__(self, name, version, parent):
        self.build_dependencies = {}

        self.package_name = name
        self.package_version = version
        self.parent = parent
        self._find_dependencies()


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
    
    def _find_dependencies(self):
        apt_pkg = apt_utils.inspect_package(self.package_name, self.package_version)
        self.build_dependencies.update(apt_pkg)

        # if self.package_name not in self.build_dependencies:
        #   self.build_dependencies[self.package_name] = []

        # self.build_dependencies[self.package_name].append({
        #   "operator": OPERATION_TRANSLATION_TABLE["="],
        #   "version": self.package_version,
        #   "from": self.parent
        # })
