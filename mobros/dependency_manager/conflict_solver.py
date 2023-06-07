"""Module that holds conflict solving and detection of dependencies"""
import sys

import mobros.utils.logger as logging
from mobros.utils import apt_utils, version_utils




# def check_deps(name, version, ideb_name, ideb_version, visited=None):
#     if visited is None:
#         visited = {}

#     pkg = DebianPackage(name, version, False)
#     deps = pkg.get_dependencies().items()
#     if ideb_name in pkg.get_dependencies():
#         version_rules = pkg.get_dependencies()[ideb_name]

#         if apt_utils.is_package_already_installed(ideb_name):
#             installed_in_consideration = {
#                 "operator": "version_eq",
#                 "version": apt_utils.get_package_installed_version(ideb_name),
#                 "from": "Installed",
#             }
#             version_rules.append(installed_in_consideration)
#         count = 0
#         for rule in version_rules:
#             if rule["operator"] == "version_eq":
#                 count += 1
#         if count > 1:
#             return False
#         candidates = find_candidate_online(ideb_name, version_rules)

#         if ideb_version in candidates:
#             # print("and its the right one " +ideb_name+ "!!! expected:"+ ideb_version + "is in "+str(candidates))
#             # print("my father is "+name+" with version "+version)
#             # print("my rules are "+str(version_rules))
#             return True

#     for dep_name, version_rules in deps:
#         if version_rules:
#             if apt_utils.is_package_already_installed(dep_name):
#                 installed_in_consideration = {
#                     "operator": "version_eq",
#                     "version": apt_utils.get_package_installed_version(dep_name),
#                     "from": "Installed",
#                 }
#                 version_rules.append(installed_in_consideration)

#             possibilities = find_candidate_online(dep_name, version_rules)
#             apt_utils.order_dpkg_versions(possibilities, reverse=True)
#             for version_dep in possibilities:
#                 my_dep_v_key = dep_name + version_dep
#                 if my_dep_v_key not in visited:
#                     visited[my_dep_v_key] = dep_name
#                     if check_deps(
#                         dep_name, version_dep, ideb_name, ideb_version, visited
#                     ):
#                         return True

def is_spot_on(version_rules):
    """Checks if in the version rules of a dependency there is an equals rule.

    Args:
        version_rules (list): list of version rules

    Returns:
        bool: True if through the version rules there is a direct version_eq
    """
    for rule in version_rules:
        if rule["operator"] == "version_eq":
            return True
    return False


# def is_there_a_solution(
#     dependency_bank, assumed_node, target_sub_dep, target_sub_dep_version
# ):
#     candidates = find_candidate_online(assumed_node, dependency_bank[assumed_node])
#     for candidate in candidates:
#         if check_deps(assumed_node, candidate, target_sub_dep, target_sub_dep_version):
#             return True, assumed_node, candidate

#     return False, None, None


# def find_if_has_option_multiparent(
#     dependency_bank, package_name, converge_version, assumed_map, curr_parent=None
# ):
#     if not curr_parent:
#         for rules in dependency_bank[package_name]:
#             if rules["from"] != "Installed":
#                 if find_if_has_option_multiparent(
#                     dependency_bank,
#                     package_name,
#                     converge_version,
#                     assumed_map,
#                     curr_parent=rules["from"],
#                 ):
#                     return True
#         return False

#     parent = curr_parent.split("=")[0]

#     if parent == "user":
#         logging.error("Unable to find a fix for this conflicts")
#         sys.exit(3)

#     version_rules = dependency_bank[parent]
#     candidates_list = find_candidate_online(parent, version_rules)
#     spot_on = len(candidates_list) == 1 and is_spot_on(version_rules)

#     if spot_on:
#         calc_info = "calculated"
#     else:
#         calc_info = "assumed"

#     if calc_info == "assumed":
#         analysis_result, candidate, candidate_version = is_there_a_solution(
#             dependency_bank, parent, package_name, converge_version
#         )
#         if analysis_result:
#             # logging.userWarning("Recovered from colision of "+package_name+" by replacing one of his ancestors "+candidate+" to "+candidate_version+"!")
#             return True

#     for rules in dependency_bank[parent]:
#         if rules["from"] != "Installed":
#             if find_if_has_option_multiparent(
#                 dependency_bank,
#                 package_name,
#                 converge_version,
#                 assumed_map,
#                 curr_parent=rules["from"],
#             ):
#                 return True

#     return False


def attempt_conflicts_solving(conflicts_list, dependency_bank, blacklist):
    """Attempts to solve conflicts detected through the dependency analysis

    Args:
        conflicts_list (list): list of conflicts
        dependency_bank (dependency_bank): Dependency manager's dependency bank
    """
    mandatory_converger_version = None

    logging.userWarning("Trying to find a solution for the conflicts")
    for conflict in conflicts_list:
        possibilities = {}
        solved = False
        for rule in conflict["rules"]:
            if rule["from"] == "Installed":
                mandatory_converger_version = rule["version"].split("-")[0]
            else:

                main_version = rule["version"].split("-")[0]
                if main_version not in possibilities:
                    possibilities[main_version] = main_version

        if mandatory_converger_version:
            pkg_origin = apt_utils.get_package_origin(conflict["name"])
            if pkg_origin is not None and "mov.ai" not in pkg_origin:
                if (
                    len(possibilities.keys()) == 1
                    and mandatory_converger_version in possibilities
                ):
                    logging.userWarning(
                        "Upgrading "
                        + conflict["name"]
                        + " since its just a new build version."
                    )
                    if conflict["name"] not in dependency_bank:
                        rule_to_blacklist = version_utils.create_version_rule("version_eq" ,mandatory_converger_version, "Installed")
                    else:
                        rule_to_blacklist = version_utils.get_rule_based_on_from(dependency_bank[conflict["name"]], "Installed")

                        dependency_bank[
                            conflict["name"]
                        ] = version_utils.remove_rule_based_on_from(
                            dependency_bank[conflict["name"]], "Installed"
                        )

                    solved = True
                    if conflict["name"] not in blacklist:
                        blacklist[conflict["name"]] = []
                    blacklist[conflict["name"]].append(rule_to_blacklist)

        if not solved:
            logging.error("Unable to solve.")
            sys.exit(1)


# def attempt_conflicts_solving(conflicts_list, tree_map, dependency_bank):
#     mandatory_converger_version = None
#     conflicts_resolved = 0

#     logging.userWarning("Trying to find a solution for the conflicts")
#     for conflict in conflicts_list:

#         if conflict["name"] not in tree_map:
#             conflicts_resolved +=1
#             logging.userWarning("Conflict might pass with recalculation :"+conflict["name"]+" !")
#             continue


#         for rule in conflict["rules"]:
#             if rule["from"]=="Installed":
#                 mandatory_converger_version=rule["version"]
#                 break


#         if mandatory_converger_version:
#             first_assumed_list=[]
#             if not find_if_has_option_multiparent(dependency_bank, conflict["name"], mandatory_converger_version,first_assumed_list):
#                 sys.exit(1)

#             conflicts_resolved += 1

#     # temp_bank={}
#     # for recalc_node in recalc_nodes.keys():
#     #     print("---"+recalc_node+"---")
#     #     if recalc_node not in temp_bank:
#     #         temp_bank[recalc_node]=[]
#     #     for node in self.node_map[recalc_node]:
#     #         print(node)
#     #         for other_recalc_node in recalc_nodes.keys():
#     #             if other_recalc_node != recalc_node:
#     #                 for parent_node in self.node_map[other_recalc_node]:
#     #                     if tree_utils.is_node_under_other(parent_node,node):

#     #                         temp_bank[recalc_node].append({"node":recalc_node,"parent":other_recalc_node})

#     # print("final result:")
#     # print(temp_bank)

#     # for recalc_node, parents in temp_bank.items():
#     #     if not parents:
#     #         # print("im "+recalc_node+" and i got no parents")
#     #         # print("-----before------------")

#     #         # for name, candidate_info in self.install_candidates.items():
#     #         #     if name in self.node_map:
#     #         #         for node in self.node_map[name]:
#     #         #             str_node=str(node)
#     #         #             if recalc_node in str_node:
#     #         #                 print("calcu is it ? "+str_node+" under "+recalc_node)
#     #         #print(self.possible_install_candidate_compromised)
#     #         #print(self.install_candidates)
#     #         print("-----after------------")
#     #         tree_utils.schedule_recalc_subtree(recalc_node, self)
#     #         print("to solve conflicts im going to register "+recalc_node+" with "+str(recalc_nodes[recalc_node]))
#     #         self.register_package(DebianPackage(recalc_node,recalc_nodes[recalc_node],False))
#     #         print(self.dependency_bank[recalc_node])
#     #         # for e in self.possible_install_candidate_compromised:
#     #         #     if e in self.node_map:
#     #         #         for node in self.node_map[e]:
#     #         #             str_node=str(node)
#     #         #             if recalc_node in str_node:
#     #         #                 print(" is it ? "+recalc_node+" under "+str_node)

#     #         # for name, candidate_info in self.install_candidates.items():
#     #         #     if name in self.node_map:
#     #         #         for node in self.node_map[name]:
#     #         #             str_node=str(node)
#     #         #             if recalc_node in str_node:
#     #         #                 print("calcu is it ? "+str_node+" under "+recalc_node)
#     # #sys.exit(1)

#     if conflicts_resolved != len (conflicts_list):
#         logging.error("Unable to resolve all conflicts "+str(conflicts_resolved)+ " vs "+str(len (conflicts_list)))
#         sys.exit(1)


# ## limited single parent
# # def find_if_has_option(self, package_name, converge_version):

# #     #print(self.install_candidates["libgssapi-krb5-2"]["from"])
# #     for node in self.node_map[package_name]:
# #         searching=True
# #         parent=node.parent.name

# #         while searching:
# #             if parent == "user":
# #                 print("im in root")
# #                 return None, None
# #             if self.install_candidates[parent]["calculation_base"] == "assumed":

# #                 # calculated_candidates=find_candidate_online(parent,self.dependency_bank[parent])

# #                 # logging.warning(str(self.dependency_bank[parent]))
# #                 logging.warning("im "+parent+" and i was assumed")
# #                 analysis_result, candidate, candidate_version= self.is_there_a_solution(parent, package_name, converge_version)
# #                 if analysis_result:
# #                     return candidate, candidate_version

# #                 #logging.error("is there a solution ? "+self.is_there_a_solution(parent,))
# #                 # if len(calculated_candidates) > 1:
# #                 #     print("cheguei aqui e sou "+parent+" : "+str(calculated_candidates))
# #                 #     sys.exit(1)
# #                 # else:
# #                 #     print("skipped "+parent + " with "+str(calculated_candidates))

# #             else:
# #                 logging.warning("im "+parent+" and i calculated")
# #             parents=[]
# #             for node in self.node_map[parent]:
# #                 if node.parent.name not in parents:
# #                     parents.append(node.parent.name)
# #             # print("my parents "+str(parents))
# #             # print("my froms "+str(self.dependency_bank[parent]))
# #             for rules in self.dependency_bank[parent]:
# #                 if rules["from"] in parents:
# #                     print("im "+parent + " and im directly influenced by "+rules["from"]+" check "+str(self.dependency_bank[parent]))


# #                 #searching=False
# #             parent_name=""
# #             for rules in self.dependency_bank[parent]:
# #                 if rules["from"] != "Installed" and rules["operator"] == "version_eq":
# #                     parent_name=rules["from"].split("=")[0]

# #             if parent_name=="":

# #                 parent_name=self.node_map[parent][0].parent.name
# #                 logging.error("n sei o que fazer depois de "+parent+" vou usar a arvore. achei este "+parent_name)
# #             parent=parent_name
# #         print("sai da procura")
# #         return None, None
# #         sys.exit(1)
