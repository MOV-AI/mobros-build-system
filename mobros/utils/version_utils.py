""" Utilitary module to deal with version related operations"""
from functools import cmp_to_key

from pydpkg import Dpkg

from mobros.utils import logger as logging


def find_lowest_top_rule(version_rules):
    """Function to find the lowest 'lower than' rule of a dependency.

    Args:
        version_rules (list): list of all version rules from the workspace

    Returns:
        version_rule: the lowest 'lower than' rule within the list or None if no 'lower than' rule found
    """
    included = True
    bottom_limit = []

    for rule in version_rules:
        if "version_lt" == rule["operator"]:
            bottom_limit.append(
                {
                    "version": rule["version"],
                    "included": not included,
                    "from": rule["from"],
                }
            )
        elif "version_lte" == rule["operator"]:
            bottom_limit.append(
                {"version": rule["version"], "included": included, "from": rule["from"]}
            )

    if len(bottom_limit) == 0:
        return None

    order_rule_versions(bottom_limit)
    return bottom_limit[0]


def find_highest_bottom_rule(version_rules):
    """Function to find the highest 'greater than' rule of a dependency.

    Args:
        version_rules (list): list of all version rules from the workspace

    Returns:
        version_rule: the highest 'greater than' rule within the list or None if no 'greater than' rule found
    """
    included = True
    top_limit = []

    for rule in version_rules:
        if "version_gt" == rule["operator"]:
            top_limit.append(
                {
                    "version": rule["version"],
                    "included": not included,
                    "from": rule["from"],
                }
            )
        elif "version_gte" == rule["operator"]:
            top_limit.append(
                {"version": rule["version"], "included": included, "from": rule["from"]}
            )

    if len(top_limit) == 0:
        return None

    order_rule_versions(top_limit, reverse=True)
    return top_limit[0]


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


def filter_through_bottom_rule(version_list, low_limit_rule, deb_name):
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
        "[filter through bottom rule] Pkg "
        + deb_name
        + ". filtering by "
        + lower_possible_version
        + ", included ? "
        + str(inclusion)
    )
    logging.debug(
        "[filter through bottom rule] Pkg "
        + deb_name
        + ". Before filter: "
        + str(version_list)
    )
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
        "[filter through bottom rule] Pkg "
        + deb_name
        + ". After filter: "
        + str(remaining_versions)
    )
    logging.debug("----------------------------------")
    return remaining_versions


def filter_through_top_rule(version_list, high_limit_rule, deb_name):
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
        "[filter through top rule] Pkg "
        + deb_name
        + ". filtering by "
        + highest_possible_version
        + ", included ? "
        + str(inclusion)
    )
    logging.debug(
        "[filter through top rule] Pkg "
        + deb_name
        + ". Before filter: "
        + str(version_list)
    )
    logging.debug("----------------------------------")

    if inclusion:
        remaining_versions = [
            i for i in version_list if compare(highest_possible_version, i) >= 0
        ]
    else:
        remaining_versions = [
            i for i in version_list if compare(highest_possible_version, i) > 0
        ]

    logging.debug(
        "[filter through top rule] Pkg "
        + deb_name
        + ". After filter: "
        + str(remaining_versions)
    )
    logging.debug("----------------------------------")
    return remaining_versions


def find_equals_rule(version_rules):
    """Function to find the first 'equals' rule of a dependency.

    Args:
        version_rules (list): list of all version rules from the workspace

    Returns:
        found: boolean that defines the success of the search
        version_rule: the first 'equals' rule within the list or None if no 'equals' rule found
    """
    equals_rule = {}
    for rule in version_rules:
        if "version_eq" == rule["operator"]:
            equals_rule = rule

    if equals_rule == {}:
        return False, None

    return True, equals_rule


def append_new_rules(dependency_bank, new_rules, key):
    """ Appends the new values from a list of version rules into the dependency bank 

    Args:
        dependency_bank (dependency_bank): dependency manager's dependency bank
        new_rules (list): list of version rules
        key (str): dependency bank map key
    """
    for rule in new_rules:
        found = False
        if key in dependency_bank:
            for known_rule in dependency_bank[key]:
                if (
                    rule["operator"] == known_rule["operator"]
                    and rule["version"] == known_rule["version"]
                    and rule["from"] == known_rule["from"]
                ):
                    found = True
        else:
            dependency_bank[key] = []

        if not found:
            dependency_bank[key].append(rule)


def remove_rule_based_on_from(rules, from_to_delete):
    """returns a new version rules list without any elements from the inputed from_to_delete

    Args:
        version_rules (list): list of all version rules
        from_to_delete (str): from key for deletion

    Returns:
        version_rules (list): filtered list
    """
    new_list = []
    for rule in rules:
        if rule["from"] != from_to_delete:
            new_list.append(rule)
    return new_list

def create_version_rule(operation, version, from_str):
    """Function to create a version_rule dict from the inputed values.

    Args:
        operation (str): comparison operator
        version (str): version
        from_str (str): from where did this dependency rule came from

    Returns:
        version_rule: Version rule dict with the inputed values.
    """
    return {
        "operator": operation,
        "version": version,
        "from": from_str
    }
