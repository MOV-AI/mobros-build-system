"""Module that contains utilitary functions to deal with apt releated operations"""

import apt
from pydpkg import Dpkg
from functools import cmp_to_key
import sys
import mobros.utils.logger as logging
from mobros.utils.utilitary import execute_shell_command_with_output

def get_package_avaiable_versions(deb_name):
    """function that gathers all installed .deb packages in an environment from a specific repository"""
    cache = apt.Cache()
    try:
      cache.update()
      cache.open()
    except apt.cache.LockFailedException as e:
      logging.warning("Unable to do apt update. Please run as sudo, or execute it before mobros!")
    for package in cache:
        if package.name == deb_name:
          return clean_apt_versions(package.versions)

#def install_package(deb_name, version):
  # cache = apt.Cache()
  # cache.update()
  # cache.open()
  # pkg = cache[deb_name]
  
  # candidate = pkg.versions.get(version)
  # pkg.candidate = candidate
  # pkg.mark_install()
  # cache.commit()
  
def install_package(deb_name, version=None, simulate=False):
  candidate=deb_name
  if version:
    candidate+="=" + version
  logging.info("Installing " + candidate)
  if not simulate:
    print("am i doing something?")
    execute_shell_command_with_output(["sudo", "apt-get", "install","-y" ,"--allow-downgrades", candidate], stop_on_error=True)
  

def clean_apt_versions(version_list):
  clean_versions=[]
  for version in version_list:
    clean_versions.append(str(version).split("=")[1])

  order_dpkg_versions(clean_versions, reverse=True)
  return clean_versions

def order_dpkg_versions(version_list, reverse=False):
    def compare(elem1,elem2):
      return Dpkg.compare_versions(elem1, elem2) 
    version_list.sort(key=cmp_to_key(compare), reverse=reverse)


def order_rule_versions(version_list, reverse=False):
    def compare(elem1,elem2):
      return Dpkg.compare_versions(elem1["version"], elem2["version"]) 
    version_list.sort(key=cmp_to_key(compare), reverse=reverse)
    
def filter_through_bottom_rule(version_list, low_limit_rule):
    def compare(elem1,elem2):
      return Dpkg.compare_versions(elem1, elem2) 

    myNumber=low_limit_rule["version"]
    inclusion=low_limit_rule["included"]
    print("my number"+myNumber)
    
    print("Of Possible "+str(version_list))
    inclusion=True
    if inclusion:
      remaining_versions = [ i for i in version_list if compare(i, myNumber) >= 0]
    else:
      remaining_versions = [ i for i in version_list if compare(i, myNumber) > 0]
    print("List after filtered through bottom rule: "+str(remaining_versions))
    return remaining_versions

def filter_through_top_rule(version_list, high_limit_rule):
    def compare(elem1,elem2):
      return Dpkg.compare_versions(elem1, elem2) 

    myNumber=high_limit_rule["version"]
    inclusion=high_limit_rule["included"]
    print("my number"+myNumber)
    
    print("Of Possible "+str(version_list))
    if inclusion:
      remaining_versions=[ i for i in version_list if compare( myNumber, i) >= 0]
    else:
      remaining_versions=[ i for i in version_list if compare( myNumber, i) > 0]
    print("List after filtered through top rule: "+str(remaining_versions))
    return remaining_versions

