"""Module that handles and keeps the information needed to generate the apt lists for install, hold and auto marking"""

from mobros.utils import apt_utils
import mobros.utils.logger as logging
from mobros.utils.utilitary import deep_copy_object

class InstallListHandler:
    """Class that holds and handles the ordered list for apt installation and marking.
    """

    def __init__(self, upgrade_installed, dependency_manager, reverse= True):
        """InstallListHandler constructor

        Args:
            upgrade_installed (bool): upgrade installed mode
            dependency_manager (dependency_manager): Dependency manager object
            reverse (bool, optional): Take in consideration the order in reverse. Defaults to True.
        """
        self.upgrade_installed = upgrade_installed
        self.dependency_manager = dependency_manager
        self.reverse = reverse

        self.package_list = []
        self.package_list_marked_auto = []
        self.package_list_marked_hold = []

    def register_ordered_element(self, deb_name, version):
        """Registers an element for installation/marking. Assummes the requests are ordered

        Args:
            deb_name (str): debian name
            version (str): debian versionb
        """
        # if (
        #     self.upgrade_installed
        #     or self.dependency_manager.is_user_requested_package(deb_name)
        #     or not apt_utils.is_package_already_installed(deb_name, version)
        # ):
        install_elem = deb_name + "=" + version
        local_name = self.dependency_manager.translate_to_local_path(install_elem)
        if local_name:
            install_elem = local_name

        self.package_list.append(install_elem)

        if not self.dependency_manager.is_user_requested_package(deb_name) and not apt_utils.is_package_already_installed(deb_name, version):
            self.package_list_marked_auto.append(deb_name)

        if self.dependency_manager.is_user_requested_package(deb_name):
            self.package_list_marked_hold.append(deb_name)

    def get_package_list_as_string(self):
        """Returns the apt install list as a string.
        """
        current_pkg_list = self.package_list

        if self.reverse:
            current_pkg_list = deep_copy_object(self.package_list)
            current_pkg_list.reverse()

        return ''.join(f"{item} " for item in current_pkg_list)

    def get_package_hold_list_as_string(self):
        """Returns the apt hold marking list as a string.
        """
        return ''.join(f"{item} " for item in self.package_list_marked_hold)

    def get_package_auto_list_as_string(self):
        """Returns the apt hold marking list as a string.
        """
        return ''.join(f"{item} " for item in self.package_list_marked_auto)

    def print_installation_report(self):
        """Prints a report with an ordered list of packages to be installed. 
        """
        current_pkg_list = self.package_list

        if self.reverse:
            current_pkg_list = deep_copy_object(self.package_list)
            current_pkg_list.reverse()

        for pkg in current_pkg_list:

            if apt_utils.is_package_local_file(pkg):
                logging.userWarning(
                        "Installing local file "
                        + pkg
                    )
                continue

            fragmented_element_info = pkg.split("=")
            deb_name = fragmented_element_info[0]
            version = fragmented_element_info[1]

            if (
                self.upgrade_installed
                or self.dependency_manager.is_user_requested_package(deb_name)
                or not apt_utils.is_package_already_installed(deb_name, version)
            ):
                if apt_utils.is_package_already_installed(deb_name):
                    logging.userWarning(
                        "Installing "
                        + deb_name
                        + "="
                        + version
                        + " (Upgrading from "
                        + apt_utils.get_package_installed_version(deb_name)
                        + ")"
                    )
                else:
                    logging.userInfo("Installing " + deb_name + "=" + version)
