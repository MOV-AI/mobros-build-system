""" Module with the ability to identify dependency conflicts and find candidate versions that fullfills the dependency tree
"""
import sys
import time
from multiprocessing import Pool, cpu_count

from anytree import DoubleStyle, Node, PreOrderIter, RenderTree
from pydpkg import Dpkg

from mobros.constants import OPERATION_TRANSLATION_TABLE
from mobros.exceptions import (
    ColisionDetectedException,
    InstallCandidateNotFoundException,
)
from mobros.types.intternal_package import PackageInterface
from mobros.utils import apt_utils
from mobros.utils import logger as logging
from mobros.utils import utilitary, version_utils


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
    """Function that is able to find the candidate version from the apt cache that passes
    the version rules from all dependencies in the workspace

    Args:
        deb_name (str): debian package name
        version_rules (list): list of all version rules from the workspace

    Returns:
        version: The candidate version to be installed from apt of a given debian package
    """
    avaiable_versions = apt_utils.get_package_avaiable_versions(deb_name)
    if not avaiable_versions:
        msg = "Unable to find online versions of package " + deb_name + "\n"
        msg += "Tip: Check if mobros was able to update your apt cache (apt update)! Either run mobros with sudo or execute 'apt update' beforehand"
        raise InstallCandidateNotFoundException(msg)

    found, equals_rule = find_equals_rule(version_rules)
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

        return equals_rule["version"]

    top_limit_rule = find_lowest_top_rule(version_rules)
    bottom_limit_rule = find_highest_bottom_rule(version_rules)

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
        return remaining_versions[0]

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
    return remaining_versions[0]


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

    version_utils.order_rule_versions(bottom_limit)
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

    version_utils.order_rule_versions(top_limit, reverse=True)
    return top_limit[0]


def check_for_multi_equals(version_rules, deb_name):
    """Function that validates if there are rules 'equals' with different versions colliding.

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

            logging.debug(
                "[Check for colisions - check for multi equals] Pkg:"
                + deb_name
                + ". Found equals rule!"
            )
            logging.debug(
                "[Check for colisions - check for multi equals] Pkg:"
                + deb_name
                + ". Dependency: "
                + deb_name
                + " has "
                + rule["version"]
                + " ( "
                + rule["operator"]
                + " ) from "
                + str(rule["from"])
            )
            rules_equals_hits.append(rule)

    if conflict_detected:
        msg = "Dependency conflict detected for dependency: " + deb_name + "\n"
        for conflict in rules_equals_hits:
            msg += (
                str(conflict["from"])
                + " expects: ("
                + conflict["operator"]
                + " "
                + conflict["version"]
                + ")\n"
            )

        raise ColisionDetectedException(msg)

    logging.debug(
        "[Check for colisions - check for multi equals] Pkg:"
        + deb_name
        + ". No Conflicts detected here!"
    )


def check_if_equals_violates_edges(version_rules, deb_name):
    """Function that validates if the 'greater than' rules do not collide with the 'lower than' rules.

    Args:
        version_rules (list): list of all version rules from the workspace
        deb_name (str): debian package name
    """
    found, equals_rule = find_equals_rule(version_rules)
    if not found:
        logging.debug(
            "[Check for colisions - check equals violates edges] Pkg:"
            + deb_name
            + ". No equals rule found for "
            + deb_name
            + "! Skipping validation."
        )
        return

    check_if_rule_violates_bottom_edges(equals_rule, version_rules, deb_name)
    check_if_rule_violates_top_edges(equals_rule, version_rules, deb_name)


def check_if_rule_violates_bottom_edges(rule_evaluated, version_rules, deb_name):
    """Function that validates if a version rule does not go against any of the 'greater than' rules.

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
                    logging.debug(
                        "[Check for colisions - check equals violates bottom edge] Pkg:"
                        + deb_name
                        + ". Colision detected!"
                    )
                    logging.debug(
                        "[Check for colisions - check equals violates bottom edge] Pkg:"
                        + deb_name
                        + ". Is "
                        + rule_evaluated["version"]
                        + "|"
                        + rule_evaluated["operator"]
                        + " coliding with "
                        + rule["version"]
                        + "|"
                        + rule["operator"]
                        + "?"
                    )
                    conflict_detected = True
                    rules_conflict_hits.append(rule)

                if rule["operator"] == "version_gt" and compare_result < 1:
                    logging.debug(
                        "[Check for colisions - check equals violates bottom edge] Pkg:"
                        + deb_name
                        + ". Colision detected!"
                    )
                    logging.debug(
                        "[Check for colisions - check equals violates bottom edge] Pkg:"
                        + deb_name
                        + ". Is "
                        + rule_evaluated["version"]
                        + "|"
                        + rule_evaluated["operator"]
                        + " coliding with "
                        + rule["version"]
                        + "|"
                        + rule["operator"]
                        + "?"
                    )
                    conflict_detected = True
                    rules_conflict_hits.append(rule)

    if conflict_detected:
        rules_conflict_hits.append(rule_evaluated)
        msg = "Dependency conflict detected for dependency: " + deb_name + "\n"
        for conflict in rules_conflict_hits:
            msg += (
                conflict["from"]
                + " expects: ("
                + conflict["operator"]
                + " "
                + conflict["version"]
                + ")\n"
            )

        raise ColisionDetectedException(msg)


def check_if_rule_violates_top_edges(rule_evaluated, version_rules, deb_name):
    """Function that validates if a version rule does not go against any of the 'lower than' rules.

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
                    logging.debug(
                        "[Check for colisions - check equals violates top edge] Pkg:"
                        + deb_name
                        + ". Colision detected!"
                    )
                    logging.debug(
                        "[Check for colisions - check equals violates top edge] Pkg:"
                        + deb_name
                        + ". Is "
                        + rule_evaluated["version"]
                        + "|"
                        + rule_evaluated["operator"]
                        + " coliding with "
                        + rule["version"]
                        + "|"
                        + rule["operator"]
                        + "?"
                    )
                    conflict_detected = True
                    rules_conflict_hits.append(rule)

                if rule["operator"] == "version_lt" and compare_result < 1:
                    logging.debug(
                        "[Check for colisions - check equals violates top edge] Pkg:"
                        + deb_name
                        + ". Colision detected!"
                    )
                    logging.debug(
                        "[Check for colisions - check equals violates top edge] Pkg:"
                        + deb_name
                        + ". Is "
                        + rule_evaluated["version"]
                        + "|"
                        + rule_evaluated["operator"]
                        + " coliding with "
                        + rule["version"]
                        + "|"
                        + rule["operator"]
                        + "?"
                    )

                    conflict_detected = True
                    rules_conflict_hits.append(rule)

    if conflict_detected:
        rules_conflict_hits.append(rule_evaluated)
        msg = "Dependency conflict detected for dependency: " + deb_name + "\n"
        for conflict in rules_conflict_hits:
            msg += (
                conflict["from"]
                + " expects: ("
                + conflict["operator"]
                + " "
                + conflict["version"]
                + ")\n"
            )

        raise ColisionDetectedException(msg)


def check_if_edges_violate_eachother(version_rules, deb_name):
    """Function that validates if 'lower than's and 'greater than' dependencies rules do not colide
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


def check_colision(dependency):
    """Function that analyses the version rules of a dependency for colission between them.

    Args:
        dependency (list): dependency information. First item is the package name, second item is the version rules.

    Returns:
        dict: dictionary that contains the execution status and error messages(in case of conflicts).
    """
    # if deb_name in self._possible_colision:
    version_rules = dependency[1]
    deb_name = dependency[0]
    try:
        if version_rules:
            check_for_colisions(deb_name, version_rules)
        return {"executionStatus": True, "message": None}
    except ColisionDetectedException as e:
        return {"executionStatus": False, "message": e.message}


def calculate_install(dependency):
    """functin that calculates a install candidate version for this package/dependnecy

    Args:
        dependency (list): dependency information. First item is the package name, second item is the version rules.

    Returns:
        dict: dictionary that contains the execution status, error message and version candidate if successfull.
    """
    dependency_name = dependency[0]
    version_rules = dependency[1]
    candidates = {}
    try:
        if version_rules:
            version = find_candidate_online(dependency_name, version_rules)
            candidates[dependency_name] = {
                "name": dependency_name,
                "version": version,
                "from": "calculated",
            }

            return {"executionStatus": True, "message": None}, candidates

        return {
            "executionStatus": False,
            "message": "Something went wrong here " + dependency_name,
        }, None

    except InstallCandidateNotFoundException as e:
        return {"executionStatus": False, "message": e.message}, None
    # self._install_candidates.append({"name": dependency_name})


class DependencyManager:
    """Class that provides the ability to scan package dependencies, analyze their colision and calculate
    the debian candidates to be installed.
    """

    def __init__(self):
        """Constructor"""
        self._dependency_bank = {}
        self._install_candidates = {}
        self._possible_colision = []
        self._possible_install_candidate_compromised = []

        self.root = Node("/")
        self.node_map = {}

    def version_rules_already_registered(self, deb_name, version_rules):
        """Checks if the version rules for this package are already registered in the dependency bank

        Args:
            deb_name (str): debian name/package name
            version_rules (version_rule []): list of version rules

        Returns:
            bool: True if the package already contains this version rules. False otherwise.
        """
        if deb_name not in self._dependency_bank:
            return False

        for version_rule in version_rules:
            for known_version_rule in self._dependency_bank[deb_name]:
                if (
                    version_rule["operator"] == known_version_rule["operator"]
                    and version_rule["version"] == known_version_rule["version"]
                ):
                    return True
        return False

    def is_user_requested_package(self, dep_name):
        """Check if a node/package is one of the requested by the user

        Args:
            dep_name (str): dependency/package name

        Returns:
            bool: True if it was requested by the user. False otherwise.
        """
        for node in self.root.children:
            if node.name == dep_name:
                return True
        return False

    # pylint: disable=R0911
    def check_if_needs_recalc_tree_branch(self, dep_name, version_rules):
        """Checks if a tree node candidate's assumption has been compromised, and needs his subtree recalculated.

        Args:
            dep_name (str): debian name
            version_rules (version_rule []): list of version rules to check if compromise node candidate assumption

        Returns:
            bool: True if needs tree recalculation. False otherwise
        """
        if dep_name not in self._install_candidates:
            logging.debug(
                "[Dependency Manager - check if tree needs recalc] Needs recalc for "
                + dep_name
                + ". It has no candidate calculated."
            )
            return True

        for rule in version_rules:
            if rule["version"] == "any":
                continue

            if (
                rule["operator"] == "version_eq"
                and rule["version"] != self._install_candidates[dep_name]["version"]
            ):
                logging.debug(
                    "[Dependency Manager - check if tree needs recalc] Needs recalc for "
                    + dep_name
                    + ". version_eq was introduced and can compromise candidate!"
                )
                return True

            if rule["operator"] in ["version_lt", "version_lte"]:
                # A lower than B = -1
                # A higher than B = 1
                compare_result = Dpkg.compare_versions(
                    rule["version"], self._install_candidates[dep_name]["version"]
                )

                if rule["operator"] == "version_lte" and compare_result < 0:
                    logging.debug(
                        "[Dependency Manager - check if tree needs recalc] Needs recalc for "
                        + dep_name
                        + ". version_lte was introduced and version is lower than the assumed one!"
                    )
                    return True

                if rule["operator"] == "version_lt" and compare_result < 1:
                    logging.debug(
                        "[Dependency Manager - check if tree needs recalc] Needs recalc for "
                        + dep_name
                        + ". version_lt was introduced and version is lower than the assumed one!"
                    )
                    return True

            if rule["operator"] in ["version_gt", "version_gte"]:
                compare_result = Dpkg.compare_versions(
                    rule["version"], self._install_candidates[dep_name]["version"]
                )

                if rule["operator"] == "version_gte" and compare_result > 0:
                    logging.debug(
                        "[Dependency Manager - check if tree needs recalc] Needs recalc for "
                        + dep_name
                        + ". version_gte was introduced and version is higher than the assumed one!"
                    )
                    return True

                if rule["operator"] == "version_gt" and compare_result > -1:
                    logging.debug(
                        "[Dependency Manager - check if tree needs recalc] Needs recalc for "
                        + dep_name
                        + ". version_gt was introduced and version is higher than the assumed one!"
                    )
                    return True

        return False

    def remove_tree_node_fingerprint(self, dep_name, version_rule):
        """Function that removes any trace of the node from the dependency manager"""
        logging.debug(
            "Removing dependency: "
            + dep_name
            + " because the tree of "
            + dep_name
            + " is being destroyed for recalculation!"
        )
        # removing all traces of dependency
        self._dependency_bank[dep_name].remove(version_rule)
        if (
            dep_name
            in self._possible_install_candidate_compromised
        ):
            self._possible_install_candidate_compromised.remove(
                dep_name
            )
        if dep_name in self._possible_colision:
            self._possible_colision.remove(dep_name)
        if dep_name in self.node_map:
            for node_instance in self.node_map[dep_name]:
                node_instance.parent = None
            del self.node_map[dep_name]

    # pylint: disable=R1702
    def schedule_recalc_subtree(self, deb_name):
        """Function to prepare a subtree to be recalculated by downloading the essencial traces of the previous one.

        Args:
            deb_name (str): package name
        """
        for node_i in self.node_map[deb_name]:
            for node in PreOrderIter(node_i):
                if node.name in self._install_candidates:
                    del self._install_candidates[node.name]

                # from this point down is complete erradication of tree nodes. They need to be reintroduced by his dependencies.
                if node.name != deb_name:
                    for rule in self._dependency_bank[node.name]:
                        pkg_source = rule["from"]
                        if "=" in rule["from"]:
                            pkg_source = rule["from"].split("=")[0]

                        if pkg_source == deb_name:
                            self.remove_tree_node_fingerprint(node.name, rule)

    def register_root_package(self, package, version, author):
        """Does the same as register package, but to be used for the user requested packages and Installed packages.
        Args:
            package (str): package name
            version (str): package version_
            author (str): Either user or Installed. Its the requester of the package to be registered.
        """
        if (
            author == "user"
            and version == ""
            and apt_utils.is_package_already_installed(package)
        ):
            logging.warning(
                "Skipping the inputed package "
                + package
                + ". Its already Installed. If you want to force it, specify a version!"
            )
            return

        if package not in self._dependency_bank:
            self._dependency_bank[package] = []

        self.register_tree_node(package, package)
        operation = ""
        if version != "":
            operation = "="

        version_rules = [
            {
                "operator": OPERATION_TRANSLATION_TABLE[operation],
                "version": version,
                "from": author,
            }
        ]

        if self.version_rules_already_registered(package, version_rules):
            if package in self._install_candidates:
                return
        else:
            self._dependency_bank[package].extend(version_rules)

        self._possible_colision.append(package)
        self._possible_install_candidate_compromised.append(package)

    def register_package(self, package, skip_installed=True):
        """Setter function to register a new package and its dependencies to the dependency bank,
            to be evaluate for dependency version colision and install candidates calculation.
        Args:
            package_name (dependency/package name): Name of the package to whose dependencies are scanned.
        """
        start = time.time()

        if not issubclass(type(package), PackageInterface):
            logging.error(
                "[Dependency_Manager - register package] Contract violated! Type registered: "
                + str(type(package))
                + " does not implement the interface: "
                + str(PackageInterface)
            )
            sys.exit(1)
        package_name = package.get_name()

        logging.debug(
            "[Dependency_Manager - register package] Package: "
            + package_name
            + " is being registered."
        )

        dependencies = package.get_dependencies()
        for dep_name, version_rules in dependencies.items():
            self.register_tree_node(package_name, dep_name)

            if dep_name not in self._dependency_bank:
                self._dependency_bank[dep_name] = []

            installed_package_version = apt_utils.get_package_installed_version(
                dep_name
            )
            if installed_package_version:
                if not skip_installed:
                    self.register_root_package(
                        dep_name, installed_package_version, "Installed"
                    )

            if self.version_rules_already_registered(dep_name, version_rules):
                if dep_name in self._install_candidates:
                    continue
                logging.debug(
                    "[Dependency_Manager - register package] Detected package "
                    + dep_name
                    + " that belongs to a recalculated tree. Has no candidate. Adding it as a install compromised."
                )
            else:
                # even if no calc is done, we register the rules
                self._dependency_bank[dep_name].extend(version_rules)

            if self.check_if_needs_recalc_tree_branch(dep_name, version_rules):
                self.schedule_recalc_subtree(dep_name)

            if dep_name not in self._install_candidates:
                if dep_name not in self._possible_colision:
                    self._possible_colision.append(dep_name)

                if dep_name not in self._possible_install_candidate_compromised:
                    self._possible_install_candidate_compromised.append(dep_name)

                logging.debug(
                    "[Dependency_Manager - register package] Identified new dependencies "
                    + dep_name
                    + ": "
                    + str(version_rules)
                )
        end = time.time()
        logging.debug("[Register package] i took " + str(end - start))

    def exists_in_tree_with_parent(self, dep_name, parent):
        """Check if node exists in tree with this specific parent

        Args:
            dep_name (str): dependency name aka node name
            parent (str): parent name

        Returns:
            bool: True if node exists with specific parent, False otherwise
        """
        if dep_name in self.node_map:
            for e in self.node_map[dep_name]:
                if e.parent.name == parent:
                    return True
        return False

    def register_tree_node(self, package_name, dep_name):
        """Register new tree entry

        Args:
            package_name (str): package name, to be used as parent
            dep_name (str): dependency name, to be used as current node
        """
        if dep_name not in self.node_map:
            if package_name not in self.node_map:  # Used by the register root package
                self.node_map[dep_name] = [Node(dep_name, self.root)]
                return

            self.node_map[dep_name] = []

        if package_name in self.node_map:
            for e in self.node_map[package_name]:
                if not self.exists_in_tree_with_parent(dep_name, package_name):
                    self.node_map[dep_name].append(Node(dep_name, e))

        # curr_node=None
        # if package_name in self.node_map:
        #     curr_node=Node(dep_name, self.node_map[package_name])
        # else:
        #     curr_node=Node(dep_name, self.root)
        # self.node_map[dep_name]=curr_node

        # if dep_name not in self.node_map:
        #     curr_node=None
        #     if package_name in self.node_map:
        #         curr_node=Node(dep_name, self.node_map[package_name])
        #     else:
        #         curr_node=Node(dep_name, self.root)
        #     self.node_map[dep_name]=curr_node

    def exclude_package(self, package_name):
        """Function to remove dependencies from the dependency bank

        Args:
            package_name (dependency/package name): Name of the catkin package dependency to be removed
        """
        if package_name in self._dependency_bank:
            del self._dependency_bank[package_name]

    def render_tree(self, print_tree=False):
        """Function to store in file and print the dependency tree

        Args:
            print_tree (bool, optional): True if tree should be printed in terminal. Defaults to False.
        """
        if print_tree:
            print(RenderTree(self.root, style=DoubleStyle()).by_attr())
        utilitary.write_to_file(
            "./tree.mobtree", RenderTree(self.root, style=DoubleStyle()).by_attr()
        )

    def check_colisions(self):
        """Function that checks if the dependencies' version ruling does't colide within them"""
        start = time.time()

        with Pool(processes=cpu_count()) as pool:
            # print(str(len(self._dependency_bank.items()))+ " vs filtered "+ str(len (list(filter(lambda x: (x[0] in self._possible_colision), self._dependency_bank.items())))))
            subthreads_colision_reports = pool.map(
                check_colision,
                list(
                    filter(
                        lambda x: (x[0] in self._possible_colision),
                        self._dependency_bank.items(),
                    )
                ),
            )
            pool.close()
            pool.join()

        problem_found = False
        for execution in subthreads_colision_reports:
            if not execution["executionStatus"]:
                logging.error(execution["message"])
                problem_found = True

        if problem_found:
            sys.exit(1)

        self._possible_colision = []

        end = time.time()
        logging.debug("[check colisions] i took " + str(end - start))

    def calculate_installs(self):
        """function that calculates from the dependency bank, a list of
        debian packages candidates for installation.
        """
        with Pool(processes=cpu_count()) as pool:
            # print(len(list(filter(lambda x: ( x[0] in self._possible_install_candidate_compromised), self._dependency_bank.items()))))
            subthreads_candidates = pool.map(
                calculate_install,
                list(
                    filter(
                        lambda x: (
                            x[0] in self._possible_install_candidate_compromised
                        ),
                        self._dependency_bank.items(),
                    )
                ),
            )
            pool.close()
            pool.join()

        problem_found = False

        for execution, sub_candidates in subthreads_candidates:
            if execution["executionStatus"]:
                for new_candidate in sub_candidates.keys():
                    self._install_candidates[new_candidate] = sub_candidates[
                        new_candidate
                    ]
            else:
                logging.error(execution["message"])
                problem_found = True

        if problem_found:
            sys.exit(1)

        self._possible_install_candidate_compromised = []

    def get_install_list(self):
        """Getter function to retrieve the calculated install list

        Returns:
            list: candidates (name,version)
        """
        return self._install_candidates.values()

    def get_version_of_candidate(self, deb_name):
        """Get the version of a candidate from the dependency manager

        Args:
            deb_name (str): debian name

        Returns:
            str: calculated candidate version
        """
        return self._install_candidates[deb_name]["version"]
