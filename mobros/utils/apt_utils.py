"""Module that contains utilitary functions to deal with apt releated operations"""
import sys

import mobros.utils.logger as logging
from mobros.constants import OPERATION_TRANSLATION_TABLE
from mobros.types.apt_cache_singleton import AptCache
from mobros.utils.utilitary import execute_shell_command
from mobros.utils.version_utils import order_dpkg_versions


def is_virtual_package(deb_name):
    """function that verifies if through a debian name, if it's a virtual package.

    Args:
        deb_name (str): debian name

    Returns:
        bool: True if package is a virtual package. False otherwise
    """
    cache = AptCache().get_cache()
    return cache.is_virtual_package(deb_name)


def inspect_package(deb_name, deb_version, upgrade_installed):
    """function that based on a deb name, gathers the information of the debian, more explicitly of his dependencies.

    Args:
        deb_name (str): debian name
        version (str, optional): version of the debian. Defaults to None.

    Returns:
        dict map: map of dictionaries that contain the dependency version, comparison_operation, package whose dependecy is from.
    """
    cache = AptCache().get_cache()

    package_dependencies = {}
    package = cache.get(deb_name)
    if package is not None:
        if deb_version == "":
            deb_version = get_package_avaiable_versions(deb_name)[0]

        specific_pkg_version = package.versions.get(deb_version)

        if not specific_pkg_version:
            logging.error(
                "Package "
                + deb_name
                + " with version "
                + deb_version
                + " is not found in the apt cache avaiable "
                + str(package.versions)
            )
            sys.exit(1)

        for dependency in specific_pkg_version.dependencies:
            dep = dependency[0]
            #            for dep in dependency.or_dependencies:
            if dep.rawtype == "Depends":
                if cache.is_virtual_package(dep.name):
                    logging.debug(
                        "Dependency " + dep.name + " is a virtual package. Skipping it"
                    )
                    continue

                if dep.name not in package_dependencies:
                    package_dependencies[dep.name] = []

                SKIP = False
                if OPERATION_TRANSLATION_TABLE[
                    str(dep.relation)
                ] == "any" and is_package_already_installed(dep.name):
                    SKIP = True

                if OPERATION_TRANSLATION_TABLE[
                    str(dep.relation)
                ] == "version_eq" and is_package_already_installed(
                    dep.name, dep.version
                ):
                    SKIP = True



                if upgrade_installed or not SKIP:
                    package_dependencies[dep.name].append(
                        {
                            "operator": OPERATION_TRANSLATION_TABLE[str(dep.relation)],
                            "version": dep.version,
                            "from": deb_name + "=" + deb_version,
                        }
                    )

        # --------------------------------------

    else:
        logging.error("Package " + deb_name + " not found in apt cache.")
        logging.error(
            "Tip: Check if mobros was able to update your apt cache (apt update)! Either run mobros with sudo or execute 'apt update' beforehand"
        )
        sys.exit(1)

    return package_dependencies


def is_package_already_installed(deb_name, version=None):
    """Function that checks if the debian is installed. If the version is also specified, it verifies that specific version is installed.

    Args:
        deb_name (str): debian name
        version (str, optional): version of the debian. Defaults to None.

    Returns:
        bool: True if package is installed. False otherwise
    """
    cache = AptCache().get_cache()
    package = cache.get(deb_name)
    if package:
        if version:
            return package.is_installed and package.installed.version == version
        return package.is_installed
    return False


def get_package_installed_version(deb_name):
    """Get the installed verion of a debian

    Args:
        deb_name (str): debian name

    Returns:
        str: installed version of the debian or None if not installed
    """
    cache = AptCache().get_cache()
    package = cache.get(deb_name)
    if package and package.is_installed:
        return package.installed.version
    return None


def get_package_avaiable_versions(deb_name):
    """function that gathers all installed .deb packages in an environment from a specific repository

    Args:
        deb_name (str): debian name

    Returns:
        str[]: list of avaiable versions of the debian or empty array if none found online
    """
    cache = AptCache().get_cache()
    package = cache.get(deb_name)

    if package is not None:
        return clean_apt_versions(package.versions)

    return []


def get_package_origin(deb_name):
    """Function that fetches the installed package origin

    Args:
        deb_name (str): debian name

    Returns:
        str: Package origin
    """
    cache = AptCache().get_cache()
    package = cache.get(deb_name)
    if package:
        if package.is_installed:
            return package.installed.origins[0].site

    return None


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
        execute_shell_command(
            ["sudo", "apt-get", "install", "-y", "--allow-downgrades", candidate],
            stop_on_error=True,
            log_output=True,
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
