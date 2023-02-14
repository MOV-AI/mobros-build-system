""" Utilitary module to deal with version related operations"""
from functools import cmp_to_key
from pydpkg import Dpkg
from mobros.utils import logger as logging


def order_dpkg_versions(version_list, reverse=False):
    """Function able to order a list of versions acording to the versioning ordering mechanic from dpkg/apt

    Args:
        version_list (list): list of versions to be ordered
        reverse (bool, optional): defines if you want reverse ordering. Defaults to False.
    """

    def compare(elem1, elem2):
        return Dpkg.compare_versions(elem1, elem2)

    version_list.sort(key=cmp_to_key(compare), reverse=reverse)


def order_rule_versions(version_list, reverse=False):
    """Function able to order a list of versions rules acording to the versioning ordering mechanic from dpkg/apt

    Args:
        version_rules_list (list): list of version rules to be ordered
        reverse (bool, optional): defines if you want reverse ordering. Defaults to False.
    """

    def compare(elem1, elem2):
        return Dpkg.compare_versions(elem1["version"], elem2["version"])

    version_list.sort(key=cmp_to_key(compare), reverse=reverse)


def filter_through_bottom_rule(version_list, low_limit_rule):
    """Function that filters a list of version rules from a 'greater than' specified rule

    Args:
        version_rules (list): list of version rules from the workspace
        low_limit_rule (version_rule): version rule object (contains the version and the operation rule).
    """

    def compare(elem1, elem2):
        return Dpkg.compare_versions(elem1, elem2)

    lower_possible_version = low_limit_rule["version"]
    inclusion = low_limit_rule["included"]
    logging.debug(
        "[filter through bottom rule] filtering by "
        + lower_possible_version
        + ", included ? "
        + str(inclusion)
    )
    logging.debug("[filter through bottom rule] Before filter: " + str(version_list))
    logging.debug("----------------------------------")

    if inclusion:
        remaining_versions = [
            i for i in version_list if compare(i, lower_possible_version) >= 0
        ]
    else:
        remaining_versions = [
            i for i in version_list if compare(i, lower_possible_version) > 0
        ]

    logging.debug(
        "[filter through bottom rule] After filter: " + str(remaining_versions)
    )
    logging.debug("----------------------------------")
    return remaining_versions


def filter_through_top_rule(version_list, high_limit_rule):
    """Function that filters a list of version rules from a 'lower than' specified rule

    Args:
        version_rules (list): list of version rules from the workspace
        high_limit_rule (version_rule): version rule object (contains the version and the operation rule).
    """

    def compare(elem1, elem2):
        return Dpkg.compare_versions(elem1, elem2)

    highest_possible_version = high_limit_rule["version"]
    inclusion = high_limit_rule["included"]

    logging.debug(
        "[filter through top rule] filtering by "
        + highest_possible_version
        + ", included ? "
        + str(inclusion)
    )
    logging.debug("[filter through top rule] Before filter: " + str(version_list))
    logging.debug("----------------------------------")

    if inclusion:
        remaining_versions = [
            i for i in version_list if compare(highest_possible_version, i) >= 0
        ]
    else:
        remaining_versions = [
            i for i in version_list if compare(highest_possible_version, i) > 0
        ]

    logging.debug("[filter through top rule] After filter: " + str(remaining_versions))
    logging.debug("----------------------------------")
    return remaining_versions
