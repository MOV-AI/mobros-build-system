""" Module with the ability to identify dependency conflicts and find candidate versions that fullfills the dependency tree
"""
import sys

from pydpkg import Dpkg

import mobros.utils.logger as logging
from mobros.utils import apt_utils
from mobros.utils import version_utils
from mobros.utils.utilitary import execute_shell_command_with_output

comparison_translation_table = {
    "version_lt": "<",
    "version_lte": "<=",
    "version_eq": "=",
    "version_gte": ">=",
    "version_gt": ">",
}

ROSDEP_RESULT_HEADER = "#apt"
ROSDEP_NEED_UPDATE_ANCHOR = "your rosdep installation has not been initialized yet"
ROSDEP_NOT_FOUND = "no rosdep rule for"


def detected_need_for_rosdep_update(cmd_output):
    """ function that evaluates if the rosdep command is requesting rosdep update

    Args:
        cmd_output (str): rosdep command output

    Returns:
        needs_update: boolean that identifies if requires rosdep update first
    """
    return ROSDEP_NEED_UPDATE_ANCHOR in str(cmd_output)


def translate_package_name(rosdep_key):
    """ Function that uses rosdep to translate a catkin package name to a debian package name

    Args:
        rosdep_key (str): catkin package name

    Returns:
        debian_pkg_name : debian package name
    """
    output = execute_shell_command_with_output(["rosdep", "resolve", rosdep_key])

    if ROSDEP_NOT_FOUND in str(output):
        logging.error(output)
        sys.exit(1)

    for line in output.splitlines():
        if ROSDEP_RESULT_HEADER not in line:
            translation = line.strip()
    return translation


def check_for_colisions(deb_name, version_rules):
    """Function that checks if the version rules list does not collide with eachother

    Args:
        deb_name (str): debian package name
        version_rules (list): list of all version rules from the workspace
    """
    check_for_multi_equals(version_rules, deb_name)
    check_if_equals_violates_edges(version_rules, deb_name)
    check_if_edges_violate_eachother(version_rules, deb_name)


def find_candidate_online(deb_name, version_rules):
    """ Function that is able to find the candidate version from the apt cache that passes
    the version rules from all dependencies in the workspace

    Args:
        deb_name (str): debian package name
        version_rules (list): list of all version rules from the workspace

    Returns:
        version: The candidate version to be installed from apt of a given debian package
    """
    avaiable_versions = apt_utils.get_package_avaiable_versions(deb_name)
    if not avaiable_versions:
        logging.error("Unable to find online versions of package " + deb_name)
        logging.error(
            "Tip: Check if mobros was able to update your apt cache (apt update)! Either run mobros with sudo or execute 'apt update' beforehand"
        )
        sys.exit(1)

    found, equals_rule = find_equals_rule(version_rules)
    if found:
        if equals_rule["version"] not in avaiable_versions:
            logging.error("Unable to find a candidate for " + deb_name)
            logging.error(
                "Filter rule: "
                + equals_rule["operator"]
                + " ("
                + equals_rule["version"]
                + " ) from "
                + equals_rule["from"]
            )
            logging.error("Avaiable online: " + str(avaiable_versions))

        return equals_rule["version"]

    top_limit_rule = find_lowest_top_rule(version_rules)
    bottom_limit_rule = find_highest_bottom_rule(version_rules)

    remaining_versions = avaiable_versions
    top_rule_message = bottom_rule_message = "any"
    if top_limit_rule:
        remaining_versions = version_utils.filter_through_top_rule(
            avaiable_versions, top_limit_rule
        )
        top_rule_message = "<"
        if top_limit_rule["included"]:
            top_rule_message += "="

        top_rule_message += (
            " (" + top_limit_rule["version"] + ") from " + top_limit_rule["from"]
        )

    if bottom_limit_rule:
        remaining_versions = version_utils.filter_through_bottom_rule(
            remaining_versions, bottom_limit_rule
        )
        bottom_rule_message = ">"
        if bottom_limit_rule["included"]:
            bottom_rule_message += "="
        bottom_rule_message += (
            " (" + bottom_limit_rule["version"] + ") from " + bottom_limit_rule["from"]
        )

    if not remaining_versions:
        logging.error("Unable to find a candidate for " + deb_name)
        logging.error("Top limit rule: " + top_rule_message)
        logging.error("Bottom limit rule: " + bottom_rule_message)
        logging.error("From the Avaiable online: " + str(avaiable_versions))
        sys.exit(1)

    logging.debug("-------------------------------------------------")
    logging.debug("[Find candidates online] After top and bottom filters, remaining versions" + str(remaining_versions))
    logging.debug("-------------------------------------------------")
    logging.debug("[Find candidates online] Final decision is: " + str(max(remaining_versions)))
    return max(remaining_versions)


def find_equals_rule(version_rules):
    """ Function to find the first 'equals' rule of a dependency.

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


def find_lowest_top_rule(version_rules):
    """ Function to find the lowest 'lower than' rule of a dependency.

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

    version_utils.order_rule_versions(bottom_limit)
    return bottom_limit[0]


def find_highest_bottom_rule(version_rules):
    """ Function to find the highest 'greater than' rule of a dependency.

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

    version_utils.order_rule_versions(top_limit, reverse=True)
    return top_limit[0]


def check_for_multi_equals(version_rules, deb_name):
    """ Function that validates if there are rules 'equals' with different versions colliding.

    Args:
        version_rules (list): list of all version rules from the workspace
        deb_name (str): debian package name
    """
    conflict_detected = False
    versions_on_rules = []
    rules_equals_hits = []
    for rule in version_rules:
        if "version_eq" in rule["operator"]:
            if rule["version"] not in versions_on_rules:
                versions_on_rules.append(rule["version"])

            if len(versions_on_rules) > 1:
                conflict_detected = True
            logging.debug("[Check for colisions - check for multi equals] Found equals rule!")
            logging.debug("[Check for colisions - check for multi equals] Dependency: " + deb_name + " has " + rule["version"] + " ( " + rule["operator"] + " ) from " + rule["from"])
            versions_on_rules.append(rule["version"])
            rules_equals_hits.append(rule)

    if conflict_detected:
        logging.error("Build dependency conflict detected for dependency: " + deb_name)
        for conflict in rules_equals_hits:
            logging.error(
                conflict["from"]
                + " expects: ("
                + conflict["operator"]
                + " "
                + conflict["version"]
                + ")"
            )
        sys.exit(1)
    logging.debug("[Check for colisions - check for multi equals] No Conflicts detected here!")


def check_if_equals_violates_edges(version_rules, deb_name):
    """ Function that validates if the 'greater than' rules do not collide with the 'lower than' rules.

    Args:
        version_rules (list): list of all version rules from the workspace
        deb_name (str): debian package name
    """
    found, equals_rule = find_equals_rule(version_rules)
    if not found:
        logging.debug("[Check for colisions - check equals violates edges] No equals rule found for " + deb_name + "! Skipping validation.")
        return

    check_if_rule_violates_bottom_edges(equals_rule, version_rules, deb_name)
    check_if_rule_violates_top_edges(equals_rule, version_rules, deb_name)


def check_if_rule_violates_bottom_edges(rule_evaluated, version_rules, deb_name):
    """ Function that validates if a version rule does not go against any of the 'greater than' rules.

    Args:
        rule_evaluated (Tuple[version,operator]): version rule to be evaluated
        version_rules (list): list of all version rules from the workspace
        deb_name (str): debian package name
    """
    conflict_detected = False
    rules_conflict_hits = []

    for rule in version_rules:
        if "version_eq" != rule["operator"]:
            if "version_gt" in rule["operator"]:
                # handle greaters (included and excluded)
                compare_result = Dpkg.compare_versions(
                    rule_evaluated["version"], rule["version"]
                )

                if rule["operator"] == "version_gte" and compare_result < 0:
                    logging.debug("[Check for colisions - check equals violates bottom edge] Colision detected!")
                    logging.debug("[Check for colisions - check equals violates bottom edge] Is " + rule_evaluated["version"] + " < " + rule["version"] + "?")
                    conflict_detected = True
                    rules_conflict_hits.append(rule)

                if rule["operator"] == "version_gt" and compare_result < 1:
                    logging.debug("[Check for colisions - check equals violates bottom edge] Colision detected!")
                    logging.debug("[Check for colisions - check equals violates bottom edge] Is " + rule_evaluated["version"] + " <= " + rule["version"] + "?")
                    conflict_detected = True
                    rules_conflict_hits.append(rule)

    if conflict_detected:
        rules_conflict_hits.append(rule_evaluated)
        logging.error("Build dependency conflict detected for dependency: " + deb_name)
        for conflict in rules_conflict_hits:
            logging.error(
                conflict["from"]
                + " expects: ("
                + conflict["operator"]
                + " "
                + conflict["version"]
                + ")"
            )
        sys.exit(1)


def check_if_rule_violates_top_edges(rule_evaluated, version_rules, deb_name):
    """ Function that validates if a version rule does not go against any of the 'lower than' rules.

    Args:
        rule_evaluated (Tuple[version,operator]): version rule to be evaluated
        version_rules (list): list of all version rules from the workspace
        deb_name (str): debian package name
    """
    conflict_detected = False
    rules_conflict_hits = []

    for rule in version_rules:
        if "version_eq" != rule["operator"]:
            # handle lowers (included and excluded)
            if "version_lt" in rule["operator"]:
                compare_result = Dpkg.compare_versions(
                    rule["version"], rule_evaluated["version"]
                )

                if rule["operator"] == "version_lte" and compare_result < 0:
                    logging.debug("[Check for colisions - check equals violates top edge] Colision detected!")
                    logging.debug("[Check for colisions - check equals violates top edge] Is " + rule_evaluated["version"] + " > " + rule["version"] + "?")
                    conflict_detected = True
                    rules_conflict_hits.append(rule)

                if rule["operator"] == "version_lt" and compare_result < 1:
                    logging.debug("[Check for colisions - check equals violates top edge] Colision detected!")
                    logging.debug("[Check for colisions - check equals violates top edge] Is " + rule_evaluated["version"] + " >= " + rule["version"] + "?")

                    conflict_detected = True
                    rules_conflict_hits.append(rule)

    if conflict_detected:
        rules_conflict_hits.append(rule_evaluated)
        logging.error("Build dependency conflict detected for dependency: " + deb_name)
        for conflict in rules_conflict_hits:
            logging.error(
                conflict["from"]
                + " expects: ("
                + conflict["operator"]
                + " "
                + conflict["version"]
                + ")"
            )
        sys.exit(1)


def check_if_edges_violate_eachother(version_rules, deb_name):
    """ Function that validates if 'lower than's and 'greater than' dependencies rules do not colide
    within the workspace

    Args:
        version_rules (list): list of version rules of a dependency (contains the operators and versions).
        deb_name (str): debian package name
    """
    for rule in version_rules:
        if "version_eq" != rule["operator"]:
            if "version_lt" in rule["operator"]:
                check_if_rule_violates_bottom_edges(rule, version_rules, deb_name)

            if "version_gt" in rule["operator"]:
                check_if_rule_violates_top_edges(rule, version_rules, deb_name)


class DependencyManager:
    """ Class that provides the ability to scan package dependencies, analyze their colision and calculate
        the debian candidates to be installed.
    """
    def __init__(self):
        """Constructor
        """
        self._dependency_bank = {}
        self._install_candidates = []

    def register_package(self, package):
        """ Setter function to register a new catkin package and its dependencies to the dependency bank,
            to be evaluate for dependency version colision and install candidates calculation.
        Args:
            package_name (dependency/package name): Name of the catkin package to whose dependencies are scanned.
        """
        package_name = package.get_name()
        logging.debug("[Dependency_Manager - register package] Package: " + package_name + " is being registered.")
        build_dependencies = package.get_build_deps()
        for dep_name, version_rules in build_dependencies.items():
            if dep_name not in self._dependency_bank:
                self._dependency_bank[dep_name] = []
                logging.debug("[Dependency_Manager - register package] Package: " + package_name + " has no build dependencies.")

            self._dependency_bank[dep_name].extend(version_rules)
            logging.debug("[Dependency_Manager - register package] Identified dependencies: " + str(version_rules))

    def exclude_package(self, package_name):
        """ Function to remove dependencies from the dependency bank

        Args:
            package_name (dependency/package name): Name of the catkin package dependency to be removed
        """
        if package_name in self._dependency_bank:
            del self._dependency_bank[package_name]

    def check_colisions(self):
        """ Function that checks if the dependencies' version ruling does't colide within them
        """
        for depend_name, version_rules in self._dependency_bank.items():
            deb_name = translate_package_name(depend_name)
            logging.debug("[Dependency_Manager - check_colisions] Dependency: " + depend_name + " has been translated to " + deb_name)
            if version_rules:
                check_for_colisions(deb_name, version_rules)

    def calculare_installs(self):
        """ function that calculates from the dependency bank, a list of
        debian packages candidates for installation.
        """
        self._install_candidates = []
        logging.info("Executing rosdep update")
        execute_shell_command_with_output(["rosdep", "update"])

        for dependency_name, version_rules in self._dependency_bank.items():
            deb_name = translate_package_name(dependency_name)
            if version_rules:
                version = find_candidate_online(
                    deb_name, version_rules
                )
                self._install_candidates.append({"name": deb_name, "version": version})

            else:
                self._install_candidates.append({"name": deb_name})

    def get_install_list(self):
        """Getter function to retrieve the calculated install list

        Returns:
            list: candidates (name,version)
        """
        return self._install_candidates
