"""Module that contains utilitary functions to deal with apt releated operations"""

import apt
from mobros.utils.version_utils import order_dpkg_versions
import mobros.utils.logger as logging
from mobros.utils.utilitary import execute_shell_command_with_output


def get_package_avaiable_versions(deb_name):
    """function that gathers all installed .deb packages in an environment from a specific repository"""
    cache = apt.Cache()
    try:
        cache.update()
        cache.open()
    except apt.cache.LockFailedException:
        logging.warning(
            "Unable to do apt update. Please run as sudo, or execute it before mobros!"
        )
    for package in cache:
        if package.name == deb_name:
            return clean_apt_versions(package.versions)
    return []


# def install_package(deb_name, version):
# cache = apt.Cache()
# cache.update()
# cache.open()
# pkg = cache[deb_name]

# candidate = pkg.versions.get(version)
# pkg.candidate = candidate
# pkg.mark_install()
# cache.commit()


def install_package(deb_name, version=None, simulate=False):
    """Function to install a debian package name

    Args:
        deb_name (str): debian package name to be installed
        version (str, optional): version to be installed. Defaults to None.
        simulate (bool, optional): defines if install should be printed only or executed. Defaults to False.
    """
    candidate = deb_name
    if version:
        candidate += "=" + version
    logging.info("Installing " + candidate)
    if not simulate:
        execute_shell_command_with_output(
            ["sudo", "apt-get", "install", "-y", "--allow-downgrades", candidate],
            stop_on_error=True,
        )


def clean_apt_versions(version_list):
    """Function that orders and strips the versions from the list returned by apt cache.

    Args:
        version_list (list): list of versions from the apt cache in the cache format

    Returns:
        list: ordered list of versions from the apt cache
    """
    clean_versions = []
    for version in version_list:
        clean_versions.append(str(version).split("=")[1])

    order_dpkg_versions(clean_versions, reverse=True)
    return clean_versions
