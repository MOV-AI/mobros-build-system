"""Module that contains utilitary functions to deal with apt releated operations"""
import sys

import mobros.utils.logger as logging
from mobros.constants import OPERATION_TRANSLATION_TABLE
from mobros.types.apt_cache_singleton import AptCache
from mobros.utils.utilitary import execute_shell_command
from mobros.utils import version_utils
from mobros.exceptions import InstallCandidateNotFoundException

def is_virtual_package(deb_name):
    """function that verifies if through a debian name, if it's a virtual package.

    Args:
        deb_name (str): debian name

    Returns:
        bool: True if package is a virtual package. False otherwise
    """
    cache = AptCache().get_cache()
    return cache.is_virtual_package(deb_name)

def find_candidate_online(deb_name, version_rules):
    """Function that is able to find the candidate version from the apt cache that passes
    the version rules from all dependencies in the workspace

    Args:
        deb_name (str): debian package name
        version_rules (list): list of all version rules from the workspace

    Returns:
        version: The candidate version to be installed from apt of a given debian package
    """
    avaiable_versions = get_package_avaiable_versions(deb_name)

    if not avaiable_versions:
        msg = "Unable to find online versions of package " + deb_name + "\n"
        msg += "Tip: Check if mobros was able to update your apt cache (apt update)! Either run mobros with sudo or execute 'apt update' beforehand"
        raise InstallCandidateNotFoundException(msg)

    found, equals_rule = version_utils.find_equals_rule(version_rules)
    if found:
        if equals_rule["version"] not in avaiable_versions:
            msg = "Unable to find a candidate for " + deb_name + "\n"
            msg += (
                "Filter rule: "
                + equals_rule["operator"]
                + " ("
                + equals_rule["version"]
                + " ) from "
                + equals_rule["from"]
                + "\n"
            )
            msg += "Avaiable online: " + str(avaiable_versions)
            raise InstallCandidateNotFoundException(msg)

        return [equals_rule["version"]]

    top_limit_rule = version_utils.find_lowest_top_rule(version_rules)
    bottom_limit_rule = version_utils.find_highest_bottom_rule(version_rules)

    remaining_versions = avaiable_versions
    top_rule_message = bottom_rule_message = "any"
    if top_limit_rule:
        remaining_versions = version_utils.filter_through_top_rule(
            avaiable_versions, top_limit_rule, deb_name
        )
        top_rule_message = "<"
        if top_limit_rule["included"]:
            top_rule_message += "="

        top_rule_message += (
            " (" + top_limit_rule["version"] + ") from " + top_limit_rule["from"]
        )

    if bottom_limit_rule:
        remaining_versions = version_utils.filter_through_bottom_rule(
            remaining_versions, bottom_limit_rule, deb_name
        )
        bottom_rule_message = ">"
        if bottom_limit_rule["included"]:
            bottom_rule_message += "="
        bottom_rule_message += (
            " (" + bottom_limit_rule["version"] + ") from " + bottom_limit_rule["from"]
        )

    if len(remaining_versions) == 1:
        logging.debug(
            "[Find candidates online] Final decision for "
            + deb_name
            + " is: "
            + str(remaining_versions[0])
        )
        return remaining_versions

    if not remaining_versions:
        msg = "Unable to find a candidate for " + deb_name + "\n"
        msg += "Top limit rule: " + top_rule_message + "\n"
        msg += "Bottom limit rule: " + bottom_rule_message + "\n"
        msg += "From the Avaiable online: " + str(avaiable_versions)
        raise InstallCandidateNotFoundException(msg)

    logging.debug("-------------------------------------------------")
    logging.debug(
        "[Find candidates online] Pkg:"
        + deb_name
        + ". After top and bottom filters, remaining versions"
        + str(remaining_versions)
    )
    logging.debug("-------------------------------------------------")
    logging.debug(
        "[Find candidates online] Pkg:"
        + deb_name
        + ". Final decision is: "
        + str(remaining_versions[0])
    )
    return remaining_versions

def get_dependency_from_ors(dependency):
    """Function to chose which OR dependency to use of the list.

    Args:
        dependency (list): list of apt OR dependencies

    Returns:
        apt_dependency: Return the chosen OR dependency that is avaiable online or installed.
    """
    for or_dep in dependency:
        operation = OPERATION_TRANSLATION_TABLE[
                    str(or_dep.relation)
                ]
        version = or_dep.version
        try:
            if not is_package_already_installed(or_dep.name):
                find_candidate_online(or_dep.name, [version_utils.create_version_rule(operation, version, "")])

            return or_dep
        except InstallCandidateNotFoundException:
            continue

    return None

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
            dep = get_dependency_from_ors(dependency)
            if not dep:
                logging.debug("Dependency of package " + deb_name + " has no online candidate. Dependency: " +str(dependency))
                continue

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

    version_utils.order_dpkg_versions(clean_versions, reverse=True)
    return clean_versions
