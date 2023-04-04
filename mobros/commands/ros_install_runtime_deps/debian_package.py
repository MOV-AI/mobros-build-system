"""Module that contains an implementation of the dependency manager package for debian"""
from mobros.utils import apt_utils


class DebianPackage:
    """Class that serializes from xml to object a catkin xml package file"""

    def __init__(self, name, version, upgrade_installed):
        self.build_dependencies = {}

        self.package_name = name
        self.package_version = version
        self.upgrade_installed = upgrade_installed
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
        apt_pkg = apt_utils.inspect_package(
            self.package_name, self.package_version, self.upgrade_installed
        )
        self.build_dependencies.update(apt_pkg)
