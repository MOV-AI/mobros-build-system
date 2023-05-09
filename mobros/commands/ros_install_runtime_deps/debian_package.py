"""Module that contains an implementation of the dependency manager package for debian"""
from os import path
import sys
from mobros.utils import apt_utils
from mobros.utils import logger as logging

class DebianPackage:
    """Class that inspects and holds the debian package info and dependencies"""

    def __init__(self, name, version, upgrade_installed):
        self.build_dependencies = {}
        self.name = name
        if apt_utils.is_package_local_file(name):

            if not path.isfile(name):
                logging.error("[DebianPackage Loader] File " + name + "does not exist!")
                sys.exit(1)

            self.package_name, self.package_version = apt_utils.get_local_deb_name_version(name)
        else:
            self.package_name = name

        self.package_version = version
        self.upgrade_installed = upgrade_installed
        self._find_dependencies()

    def get_dependencies(self):
        """Getter function to retrieve the package dependencies..

        Returns:
            list: list of dependencies of the debian package.
        """
        return self.build_dependencies

    def get_name(self):
        """Getter function to retrieve the package name

        Returns:
           str: debian package name
        """
        return self.package_name

    def _find_dependencies(self):
        apt_pkg = apt_utils.inspect_package(
            self.name, self.package_version, self.upgrade_installed
        )
        self.build_dependencies.update(apt_pkg)
