"""Module for tree operation utilitary"""
from anytree import LevelOrderGroupIter, PreOrderIter, Node
from pydpkg import Dpkg
import mobros.utils.logger as logging

def overwrite_node_in_global_map(tree_map, node_name, parent_name, new_node):
    """Overwrite node in the map used by the dependency tree.

    Args:
        tree_map (map): Global map that registers all known nodes
        node_name (str): name of the node that will be overwritten
        parent_name (str): parent of the node that we want to overwrite
        new_node (Node): Node that will be used to overwrite the old one
    """
    for e in tree_map[node_name]:
        if e.parent.name == parent_name:
            tree_map[node_name].remove(e)

    tree_map[node_name].append(new_node)

def clone_subtree(tree_map, tree_to_copy_from, new_node):
    """clones the whole subtree into another tree node.

    Args:
        tree_map (map): Global map that registers all known nodes
        tree_to_copy_from (Node): node from where the sub tree will be cloned
        new_node (Node): target node that will contain a clone of the source tree
    """
    local_map={}
    for layers in LevelOrderGroupIter(tree_to_copy_from, filter_=lambda n: n.name != tree_to_copy_from.name):
        for layer in layers:
            if layer.parent.name == new_node.name:
                local_map[layer.name] = Node(layer.name, new_node)
            else:
                local_map[layer.name] = Node(layer.name, local_map[layer.parent.name])
            overwrite_node_in_global_map(tree_map, layer.name, layer.parent.name, local_map[layer.name])

def remove_node_from_lost(tree_map, package_name, lost_nodes_root):
    """_summary_

    Args:
        tree_map (map): Global map that registers all known nodes
        package_name (str): Package name to be removed from the global tree map
        lost_nodes_root (Node): Node root of all packages that are lost during the dependency scanning.
    """
    for e in tree_map[package_name]:
        if e.parent == lost_nodes_root:
            e.parent = None
            tree_map[package_name].remove(e)


# pylint: disable=R0911
def check_if_needs_recalc_tree_branch(dep_name, version_rules, dependency_manager):
    """Checks if a tree node candidate's assumption has been compromised, and needs his subtree recalculated.

    Args:
        dep_name (str): debian name
        version_rules (version_rule []): list of version rules to check if compromise node candidate assumption

    Returns:
        bool: True if needs tree recalculation. False otherwise
    """
    if dep_name not in dependency_manager.install_candidates:
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
            and rule["version"] != dependency_manager.install_candidates[dep_name]["version"]
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
                rule["version"], dependency_manager.install_candidates[dep_name]["version"]
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
                rule["version"], dependency_manager.install_candidates[dep_name]["version"]
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


def remove_tree_node_fingerprint(dep_name, version_rule, dependency_manager):
    """Function that removes any trace of the node from the dependency manager"""
    logging.debug(
        "Removing dependency: "
        + dep_name
        + " because the tree of "
        + dep_name
        + " is being destroyed for recalculation!"
    )
    # removing all traces of dependency
    dependency_manager.dependency_bank[dep_name].remove(version_rule)
    if (
        dep_name
        in dependency_manager.possible_install_candidate_compromised
    ):
        dependency_manager.possible_install_candidate_compromised.remove(
            dep_name
        )
    if dep_name in dependency_manager.possible_colision:
        dependency_manager.possible_colision.remove(dep_name)
    if dep_name in dependency_manager.node_map:
        for node_instance in dependency_manager.node_map[dep_name]:
            node_instance.parent = None
        del dependency_manager.node_map[dep_name]

# pylint: disable=R1702
def schedule_recalc_subtree(deb_name, dependency_manager):
    """Function to prepare a subtree to be recalculated by downloading the essencial traces of the previous one.

    Args:
        deb_name (str): package name
    """
    for node_i in dependency_manager.node_map[deb_name]:
        for node in PreOrderIter(node_i):
            if node.name in dependency_manager.install_candidates:
                del dependency_manager.install_candidates[node.name]

            # from this point down is complete erradication of tree nodes. They need to be reintroduced by his dependencies.
            if node.name != deb_name:
                for rule in dependency_manager.dependency_bank[node.name]:
                    pkg_source = rule["from"]
                    if "=" in rule["from"]:
                        pkg_source = rule["from"].split("=")[0]

                    if pkg_source == deb_name:
                        remove_tree_node_fingerprint(node.name, rule, dependency_manager)

def exists_in_tree_with_parent(dep_name, parent, tree_map):
    """Check if node exists in tree with this specific parent

    Args:
        dep_name (str): dependency name aka node name
        parent (str): parent name

    Returns:
        bool: True if node exists with specific parent, False otherwise
    """
    if dep_name in tree_map:
        for e in tree_map[dep_name]:
            if e.parent.name == parent:
                return True
    return False

def register_sub_root_node(dependency_manager, package_name):
    """register a node that is directly under root. Means its a user requested package

    Args:
        package_name (str): package name
    """
    if package_name not in dependency_manager.node_map:
        dependency_manager.node_map[package_name] = []

    package_node = None
    if not exists_in_tree_with_parent(package_name, dependency_manager.root.name, dependency_manager.node_map):
        if len(dependency_manager.node_map[package_name]) > 0:
            package_node = Node(package_name, dependency_manager.root)
            clone_subtree(dependency_manager.node_map, dependency_manager.node_map[package_name][0], package_node)
            remove_node_from_lost(dependency_manager.node_map, package_name, dependency_manager.lost_nodes_group)

        else:
            package_node = Node(package_name, dependency_manager.root)

        dependency_manager.node_map[package_name].append(package_node)
