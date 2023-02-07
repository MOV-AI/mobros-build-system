from mobros.utils.utilitary import execute_shell_command_with_output
from mobros.utils.apt_utils import get_package_avaiable_versions, order_rule_versions, filter_through_bottom_rule, filter_through_top_rule
from pydpkg import Dpkg
import mobros.utils.logger as logging
import sys
comparison_translation_table = {
    "version_lt": "<",
    "version_lte": "<=",
    "version_eq": "=",
    "version_gte": ">=",
    "version_gt": ">",
}

ROSDEP_RESULT_HEADER="#apt"
ROSDEP_NEED_UPDATE_ANCHOR="your rosdep installation has not been initialized yet"
ROSDEP_NOT_FOUND="no rosdep rule for"
def detected_need_for_rosdep_update(cmd_output):

  return ROSDEP_NEED_UPDATE_ANCHOR in str(cmd_output)

def translate_package_name(rosdep_key):
  output = execute_shell_command_with_output(["rosdep", "resolve", rosdep_key])

  if ROSDEP_NOT_FOUND in str(output):
    logging.error(output)
    sys.exit(1)
    
  for line in output.splitlines():
    if ROSDEP_RESULT_HEADER not in line:
      translation=line.strip()
  return translation

def check_for_colisions(deb_name, version_rules):
  check_for_multi_equals(version_rules, deb_name)
  check_if_equals_violates_edges(version_rules, deb_name)
  check_if_edges_violate_eachother(version_rules, deb_name)

def find_candidate_online(deb_name, version_rules):
  avaiable_versions = get_package_avaiable_versions(deb_name)
  if not avaiable_versions:
    logging.error("Unable to find online versions of package "+deb_name)
    logging.error("Tip: Check if mobros was able to update your apt cache (apt update)! Either run mobros with sudo or execute 'apt update' beforehand")
    sys.exit(1)
    
  found, equals_rule = find_equals_rule(version_rules)
  if found:
    if equals_rule["version"] in avaiable_versions:
      return equals_rule["version"]
    else:
      logging.error("Unable to find a candidate for "+deb_name)
      logging.error("Filter rule: "+equals_rule["operator"]+" ("+equals_rule["version"]+" ) from "+ equals_rule["from"])
      logging.error("Avaiable online: "+str(avaiable_versions))


  top_limit_rule = find_lowest_top_rule(version_rules)
  bottom_limit_rule = find_highest_bottom_rule(version_rules)
  
  remaining_versions=avaiable_versions
  top_rule_message = bottom_rule_message="any"
  if top_limit_rule:
    remaining_versions=filter_through_top_rule(avaiable_versions, top_limit_rule)
    top_rule_message="<"
    if top_limit_rule["included"]:
      top_rule_message+="="

    top_rule_message+=" ("+top_limit_rule["version"]+") from "+top_limit_rule["from"]

  if bottom_limit_rule:

    remaining_versions=filter_through_bottom_rule(remaining_versions, bottom_limit_rule)
    bottom_rule_message= ">"
    if bottom_limit_rule["included"]:
      bottom_rule_message+="="
    bottom_rule_message+=" ("+bottom_limit_rule["version"]+") from "+bottom_limit_rule["from"]
  
  if remaining_versions:
    print("final result is of "+str(remaining_versions))
    print("i chose "+str(max(remaining_versions)))
    return max(remaining_versions)
  else:
    logging.error("Unable to find a candidate for "+deb_name)
    logging.error("Top limit rule: "+top_rule_message)
    logging.error("Bottom limit rule: "+bottom_rule_message)
    logging.error("From the Avaiable online: "+str(avaiable_versions))

def find_equals_rule(version_rules):
  equals_rule={}
  for rule in version_rules:
    if "version_eq" == rule["operator"]:
      equals_rule=rule
  
  if equals_rule == {}:
    return False, None
  
  return True, equals_rule

def find_lowest_top_rule(version_rules):
  included=True
  bottom_limit=[]
  
  for rule in version_rules:
    if "version_lt" in rule["operator"]:
      bottom_limit.append({"version":rule["version"],"included": not included, "from": rule["from"] })
    elif "version_lte" in rule["operator"]:
      bottom_limit.append({"version":rule["version"],"included": included, "from": rule["from"]})
  
  if len(bottom_limit) == 0:
    return None
  
  order_rule_versions(bottom_limit)
  return bottom_limit[0]

def find_highest_bottom_rule(version_rules):
  included=True
  top_limit=[]
  
  for rule in version_rules:
    if "version_gt" in rule["operator"]:
      top_limit.append({"version":rule["version"],"included": not included, "from": rule["from"] })
    elif "version_gte" in rule["operator"]:
      top_limit.append({"version":rule["version"],"included": included, "from": rule["from"] })
  
  if len(top_limit) == 0:
    return None 
  
  order_rule_versions(top_limit, reverse=True)
  return top_limit[0]

def check_for_multi_equals(version_rules, deb_name):
  conflict_detected=False
  versions_on_rules=[]
  rules_equals_hits=[]
  for rule in version_rules:
    if "version_eq" in rule["operator"]:
      if rule["version"] not in versions_on_rules:
        versions_on_rules.append(rule["version"])
        
      if len(versions_on_rules) > 1:
        conflict_detected=True

      versions_on_rules.append(rule["version"])
      rules_equals_hits.append(rule)
  
  if conflict_detected:
    logging.error("Build dependency conflict detected for dependency: "+deb_name)
    for conflict in rules_equals_hits:
      logging.error( conflict["from"] + " expects: ("+conflict["operator"]+ " "+ conflict["version"]+")")
    sys.exit(1)

def check_if_equals_violates_edges(version_rules, deb_name):

  found, equals_rule = find_equals_rule(version_rules)
  if not found:
    return

  check_if_rule_violates_bottom_edges(equals_rule, version_rules, deb_name)
  check_if_rule_violates_top_edges(equals_rule, version_rules, deb_name)

def check_if_rule_violates_bottom_edges(rule_evaluated, version_rules, deb_name):
  conflict_detected=False
  rules_conflict_hits=[]

  for rule in version_rules:
    if "version_eq" != rule["operator"]:    
      if "version_gt" in rule["operator"]:
        #handle greaters (included and excluded)
        compare_result = Dpkg.compare_versions(rule_evaluated["version"], rule["version"])
        if rule["operator"] == "version_gte" and compare_result < 0:
          conflict_detected=True
          rules_conflict_hits.append(rule)

        if rule["operator"] == "version_gt" and compare_result < 1:
          conflict_detected=True
          rules_conflict_hits.append(rule)
        
  
  if conflict_detected:
    rules_conflict_hits.append(rule_evaluated)
    logging.error("Build dependency conflict detected for dependency: "+deb_name)
    for conflict in rules_conflict_hits:
      logging.error( conflict["from"] + " expects: ("+conflict["operator"]+ " "+ conflict["version"]+")")
    sys.exit(1)

def check_if_rule_violates_top_edges(rule_evaluated, version_rules, deb_name):
  conflict_detected=False
  rules_conflict_hits=[]

  for rule in version_rules:
    if "version_eq" != rule["operator"]:
      #handle lowers (included and excluded)
      if "version_lt" in rule["operator"]:
        compare_result = Dpkg.compare_versions(rule["version"], rule_evaluated["version"])

        if rule["operator"] == "version_lte" and compare_result < 0:
          conflict_detected=True
          rules_conflict_hits.append(rule)

        if rule["operator"] == "version_lt" and compare_result < 1:
          conflict_detected=True
          rules_conflict_hits.append(rule)

  
  if conflict_detected:
    rules_conflict_hits.append(rule_evaluated)
    logging.error("Build dependency conflict detected for dependency: "+deb_name)
    for conflict in rules_conflict_hits:
      logging.error( conflict["from"] + " expects: ("+conflict["operator"]+ " "+ conflict["version"]+")")
    sys.exit(1)

def check_if_edges_violate_eachother(version_rules, deb_name):
  for rule in version_rules:
    if "version_eq" != rule["operator"]:
      if "version_lt" in rule["operator"]:
        check_if_rule_violates_bottom_edges(rule, version_rules, deb_name)
        
      if "version_gt" in rule["operator"]:
        check_if_rule_violates_top_edges(rule, version_rules, deb_name)

class DependencyManager:
  def __init__(self):
    self._dependency_bank={}
    self._install_candidates=[]

  def register_package(self, package):
    package_name=package.get_name()
    build_dependencies=package.get_build_deps()
    for dep_key in build_dependencies.keys():
      if dep_key not in self._dependency_bank:
        self._dependency_bank[dep_key]=[]
      self._dependency_bank[dep_key].extend(build_dependencies[dep_key])

  def exclude_package(self, package_name):
    if package_name in self._dependency_bank:
      del self._dependency_bank[package_name]
    
  def check_colisions(self):
    
    for dep_key in self._dependency_bank.keys():
      deb_name=translate_package_name(dep_key)
      if self._dependency_bank[dep_key]:
        check_for_colisions(deb_name, self._dependency_bank[dep_key])
      
  def calculare_installs(self):
    self._install_candidates=[]
    logging.info("Executing rosdep update")
    execute_shell_command_with_output(["rosdep", "update"])
    
    for dep_key in self._dependency_bank.keys():
      deb_name=translate_package_name(dep_key)
      if self._dependency_bank[dep_key]:
        version = find_candidate_online(deb_name, self._dependency_bank[dep_key])
        self._install_candidates.append({"name":deb_name, "version":version})

      else:
        self._install_candidates.append({"name":deb_name})

  def get_install_list(self):
    return self._install_candidates