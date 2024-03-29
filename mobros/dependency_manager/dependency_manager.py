""" Module to identify dependency conflicts and calculate install candidate versions"""
import sys
import time

from anytree import DoubleStyle, Node, RenderTree
from pydpkg import Dpkg

from mobros.commands.ros_install_build_deps.catkin_package import CatkinPackage
from mobros.constants import OPERATION_TRANSLATION_TABLE
from mobros.dependency_manager import conflict_solver
from mobros.exceptions import (
    ColisionDetectedException,
    InstallCandidateNotFoundException,
)
from mobros.types.intternal_package import PackageInterface
from mobros.utils import apt_utils
from mobros.utils import logger as logging
from mobros.utils import tree_utils, utilitary, version_utils

UNIDENTIFIED = "undentified"
INDIRECT_INVOLVEMENT = "stuff"


def check_for_colisions(deb_name, version_rules):
    """Function that checks if the version rules list does not collide with eachother

    Args:
        deb_name (str): debian package name
        version_rules (list): list of all version rules from the workspace
    """
    check_for_multi_equals(version_rules, deb_name)
    check_if_equals_violates_edges(version_rules, deb_name)
    check_if_edges_violate_eachother(version_rules, deb_name)


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

        raise ColisionDetectedException(
            {"name": deb_name, "rules": rules_equals_hits}
        )

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
    found, equals_rule = version_utils.find_equals_rule(version_rules)
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

        raise ColisionDetectedException(
            {"name": deb_name, "rules": rules_conflict_hits}
        )


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

        raise ColisionDetectedException(
            {"name": deb_name, "rules": rules_conflict_hits}
        )


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
        return {
            "executionStatus": False,
            "conflicts": e.get_conflicts(),
        }


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
            candidates_list = apt_utils.find_candidate_online(
                dependency_name, version_rules
            )
            spot_on = len(candidates_list) == 1 and conflict_solver.is_spot_on(
                version_rules
            )

            if spot_on:
                calc_info = "calculated"
            else:
                calc_info = "assumed"

            version = candidates_list[0]
            candidates[dependency_name] = {
                "name": dependency_name,
                "version": version,
                "calculation_base": calc_info,
                "spotOn": spot_on,
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

    # pylint: disable=R0902
    def __init__(self):
        """Constructor"""
        self.dependency_bank = {}
        self.conflict_solving = False
        self.skip_installed = False
        self.install_candidates = {}
        self.possible_colision = []
        self.possible_install_candidate_compromised = []
        self.local_packages = {}
        self.blacklist = {}
        self.outside_tree_analyzed_packages = {}

        self.root = Node("/")
        self.node_map = {}
        self.lost_nodes_group = Node(UNIDENTIFIED, self.root)
        self.involved_nodes = Node(INDIRECT_INVOLVEMENT, self.root)

    def _version_rules_already_registered(self, deb_name, version_rules):
        """Checks if the version rules for this package are already registered in the dependency bank

        Args:
            deb_name (str): debian name/package name
            version_rules (version_rule []): list of version rules

        Returns:
            bool: True if the package already contains this version rules. False otherwise.
        """
        if deb_name not in self.dependency_bank:
            return False

        found_existing_rule = 0
        for version_rule in version_rules:
            for known_version_rule in self.dependency_bank[deb_name]:
                if (
                    version_rule["operator"] == known_version_rule["operator"]
                    and version_rule["version"] == known_version_rule["version"]
                ):
                    found_existing_rule = found_existing_rule + 1

        return found_existing_rule == len(version_rules)

    def is_user_requested_package(self, dep_name):
        """Check if a node/package is one of the requested by the user

        Args:
            dep_name (str): dependency/package name

        Returns:
            bool: True if it was requested by the user. False otherwise.
        """
        if dep_name in self.dependency_bank:
            for rules in self.dependency_bank[dep_name]:
                if rules["from"] == "user":
                    return True
        return False

    def register_local_package(self, file_path, package_name, version):
        """Register package as local package

        Args:
            file_path (str): local package full path
            package_name (str): package name
            version (str): package version
        """
        self.local_packages[package_name + "=" + version] = file_path

    def register_indirect_package(self, package_name, version_rules):
        """Register packages that are outside of the dependency tree

        Args:
            package (str): package name
            version_rules (version_rules): package version rules
        """
        if package_name not in self.node_map:
            self.node_map[package_name] = []
            self.node_map[package_name].append(
                Node(package_name, self.involved_nodes)
            )
        if package_name not in self.dependency_bank:
            self.dependency_bank[package_name] = []

        version_utils.append_new_rules(self.dependency_bank, version_rules, package_name)

        self.possible_colision.append(package_name)
        self.possible_install_candidate_compromised.append(package_name)

    # pylint: disable=R0912
    def register_root_package(self, package, version, author):
        """Does the same as register package, but to be used for the user requested packages and Installed packages.
        Args:
            package (str): package name
            version (str): package version_
            author (str): Either user or Installed. Its the requester of the package to be registered.
        """

        if author == "user":
            if version == "" and apt_utils.is_package_already_installed(package):
                logging.warning(
                    "Skipping the inputed package "
                    + package
                    + ". Its already Installed. If you want to force it, specify a version!"
                )
                return

            if version != "" and apt_utils.is_package_already_installed(
                package, version
            ):
                tree_utils.register_sub_root_node(self, package)
                version_rules = [
                    {
                        "operator": OPERATION_TRANSLATION_TABLE["="],
                        "version": version,
                        "from": author,
                    }
                ]
                version_utils.append_new_rules(self.dependency_bank, version_rules, package)

                if package not in self.install_candidates:
                    self.install_candidates[package] = {
                        "name": package,
                        "version": version,
                        "calculation_base": "calculated",
                        "spotOn": True,
                    }
                    return
            # If the package registered is from user, override the installed rules.
            if package in self.dependency_bank:
                for version_rule in self.dependency_bank[package]:
                    if version_rule["from"] == "Installed":
                        self.dependency_bank[package].remove(version_rule)

            tree_utils.register_sub_root_node(self, package)

        if package not in self.dependency_bank:
            self.dependency_bank[package] = []

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

        if self._version_rules_already_registered(package, version_rules):
            if package in self.install_candidates:
                return
        else:
            version_utils.append_new_rules(self.dependency_bank, version_rules, package)

        self.possible_colision.append(package)

        if package + "=" + version in self.local_packages:
            if package not in self.install_candidates:

                # register local deb in calculated candidates. We cant calculate it as it might be locally generated and not yet avaiable in the apt cache.
                self.install_candidates[package] = {
                "name": package,
                "version": version,
                "calculation_base": "calculated",
                "spotOn": True,
            }
        else:
            self.possible_install_candidate_compromised.append(package)

    # pylint: disable=R1702,R0912
    def _analyze_package_dependencies(self, package, dependencies, skip_installed):
        package_name = package.get_name()

        for dep_name, version_rules in dependencies.items():
            self.register_tree_node(package_name, dep_name)
            if dep_name not in self.dependency_bank:
                self.dependency_bank[dep_name] = []

            installed_package_version = apt_utils.get_package_installed_version(
                dep_name
            )
            if not isinstance(package, CatkinPackage):
                self.conflict_solving = True
                if installed_package_version:
                    if not skip_installed and not self.is_user_requested_package(
                        dep_name
                    ):
                        installed_is_blackisted=False
                        if dep_name in self.blacklist:
                            installed_rule = version_utils.get_rule_based_on_from(self.blacklist[dep_name], "Installed")
                            if installed_rule["version"] == installed_package_version:
                                installed_is_blackisted=True
                        if not installed_is_blackisted:
                            self.register_root_package(
                                dep_name, installed_package_version, "Installed"
                            )

            if self._version_rules_already_registered(dep_name, version_rules):
                if dep_name in self.install_candidates:
                    continue
                logging.debug(
                    "[Dependency_Manager - register package] Detected package "
                    + dep_name
                    + " that belongs to a recalculated tree. Has no candidate. Adding it as a install compromised."
                )
            else:
                # even if no calc is done, we register the rules
                version_utils.append_new_rules(
                    self.dependency_bank, version_rules, dep_name
                )

            if dep_name in self.install_candidates:
                if tree_utils.check_if_needs_recalc_tree_branch(
                    dep_name, version_rules, self
                ):
                    tree_utils.schedule_recalc_subtree(dep_name, self)

            if dep_name not in self.install_candidates:
                if dep_name not in self.possible_colision:
                    self.possible_colision.append(dep_name)

                if dep_name not in self.possible_install_candidate_compromised:
                    self.possible_install_candidate_compromised.append(dep_name)

                logging.debug(
                    "[Dependency_Manager - register package] Identified new dependencies "
                    + dep_name
                    + ": "
                    + str(version_rules)
                )

    def register_package(self, package, skip_installed=True):
        """Setter function to register a new package and its dependencies to the dependency bank,
            to be evaluate for dependency version colision and install candidates calculation.
        Args:
            package_name (dependency/package name): Name of the package to whose dependencies are scanned.
        """
        start = time.time()

        if not self.skip_installed and skip_installed:
            self.skip_installed = skip_installed

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
        self._analyze_package_dependencies(package, dependencies, skip_installed)
        end = time.time()
        logging.debug("[Register package] i took " + str(end - start))

    def register_tree_node(self, package_name, dep_name):
        """Register new tree entry

        Args:
            package_name (str): package name, to be used as parent
            dep_name (str): dependency name, to be used as current node
        """
        if dep_name not in self.node_map:
            self.node_map[dep_name] = []

        if package_name not in self.node_map:
            self.node_map[package_name] = []
            self.node_map[package_name].append(
                Node(package_name, self.lost_nodes_group)
            )

        if package_name in self.node_map:
            for e in self.node_map[package_name]:
                if not tree_utils.exists_in_tree_with_parent(
                    dep_name, package_name, self.node_map
                ):
                    new_node = Node(dep_name, e)
                    if len(self.node_map[dep_name]) > 0:
                        for node in self.node_map[dep_name]:
                            if node.children:
                                tree_utils.clone_subtree(
                                    self.node_map, node, new_node, overwrite=True
                                )
                                break
                    self.node_map[dep_name].append(new_node)

    def exclude_package(self, package_name):
        """Function to remove dependencies from the dependency bank

        Args:
            package_name (dependency/package name): Name of the catkin package dependency to be removed
        """
        if package_name in self.dependency_bank:
            del self.dependency_bank[package_name]

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


        subthreads_colision_reports = utilitary.parrallel_execute_function(check_colision,
                                             list(
                                                filter(
                                                    lambda x: (x[0] in self.possible_colision),
                                                    self.dependency_bank.items(),
                                                )
                                            ))

        problem_found = False
        conflicts_list = []
        for execution in subthreads_colision_reports:
            if not execution["executionStatus"]:
                logging.warning(version_utils.pretify_version_conflicts(execution["conflicts"]["name"], execution["conflicts"]["rules"]))
                problem_found = True
                conflicts_list.append(execution["conflicts"])

        if problem_found:
            self.render_tree()
            if self.conflict_solving:
                conflict_solver.attempt_conflicts_solving(
                    conflicts_list, self.dependency_bank, self.blacklist
                )
                logging.userWarning("Conflicts might be fixed. Continuing.")
            else:
                sys.exit(1)

        self.possible_colision = []

        end = time.time()
        logging.debug("[check colisions] i took " + str(end - start))

    def calculate_installs(self):
        """function that calculates from the dependency bank, a list of
        debian packages candidates for installation.
        """

        subthreads_candidates = utilitary.parrallel_execute_function(calculate_install,
                                             list(
                                                filter(
                                                    lambda x: (x[0] in self.possible_install_candidate_compromised),
                                                    self.dependency_bank.items(),
                                                ),
                                            ))

        problem_found = False

        for execution, sub_candidates in subthreads_candidates:
            if execution["executionStatus"]:
                for new_candidate in sub_candidates.keys():
                    self.install_candidates[new_candidate] = sub_candidates[
                        new_candidate
                    ]
            else:
                logging.error(execution["message"])
                problem_found = True

        if problem_found:
            self.render_tree()
            sys.exit(1)

        if self.skip_installed:
            self.possible_install_candidate_compromised = []
            return

        subthreads_colision_reports = utilitary.parrallel_execute_function(apt_utils.package_impacts_installed_dependencies,
                                             list(
                                                filter(
                                                    lambda x: (x[0] in self.possible_install_candidate_compromised),
                                                    self.install_candidates.items(),
                                                ),
                                            ))

        self.possible_install_candidate_compromised = []

        registered_packages = False
        for colision in subthreads_colision_reports:
            if colision:

                dep_version_rule = version_utils.create_version_rule(colision["dependency"]["operation"], self.install_candidates[colision["dependency"]["name"]]["version"], "")

                candidates = apt_utils.find_candidates_online_fullfilling_dependency(colision["name"], colision["dependency"]["name"], dep_version_rule)
                self.render_tree()
                if len(candidates) == 0:
                    logging.error("Unable to solve.")
                    sys.exit(1)

                if self.conflict_solving:
                    rules = [version_utils.create_version_rule("version_eq", colision["version"], "Installed"),
                             version_utils.create_version_rule("version_eq", candidates[0], "mobros")
                             ]

                    self.register_indirect_package(colision["name"], rules)
                    logging.userWarning("Checking if using the version " + candidates[0] + " of " + colision["name"] + " solves the conflict.")
                    conflict_solver.attempt_conflicts_solving(
                        [{"name" : colision["name"], "rules" : rules}], self.dependency_bank, self.blacklist
                    )

                    registered_packages = True

        if registered_packages:
            self.calculate_installs()

    def get_install_list(self):
        """Getter function to retrieve the calculated install list

        Returns:
            list: candidates (name,version)
        """
        return self.install_candidates.values()

    def check_if_any_depends_on(self, deb_name, deb_version):
        """Check if any package depends on the inputed package

        Args:
            deb_name (str): package name
            deb_version (str): package version

        Returns:
            boolean: True if there is any package depending on provided one.
        """
        for _, version_rules in self.dependency_bank.items():
            for rule in version_rules:
                if rule["from"] == deb_name + "=" + deb_version:
                    return True

        return False

    def get_version_of_candidate(self, deb_name):
        """Get the version of a candidate from the dependency manager

        Args:
            deb_name (str): debian name

        Returns:
            str: calculated candidate version
        """

        return self.install_candidates[deb_name]["version"]

    def has_candidate_calculated(self, deb_name):
        """Check if this deb has a candidate version

        Args:
            deb_name (str): debian name

        Returns:
            boolean: true if it has a calculated candidate version
        """
        return deb_name in self.install_candidates

    def is_local_package(self, deb_name_version):
        """Check if package is an local package inputed by the user

        Args:
            deb_name_version (str): package name and package version concatted

        Returns:
            boolean: True if local package. False otherwise.
        """
        return deb_name_version in self.local_packages

    def translate_to_local_path(self, deb_name_version):
        """translate package name and version to local package path

        Args:
            deb_name_version (str): package name and package version concatted

        Returns:
            str: local package name
        """
        if self.is_local_package(deb_name_version):
            return self.local_packages[deb_name_version]
        return None
