"""Module that contains utilitary functions to deal with apt releated operations"""

import apt
from pydpkg import Dpkg
from functools import cmp_to_key

def get_package_avaiable_versions(deb_name):
    """function that gathers all installed .deb packages in an environment from a specific repository"""

    cache = apt.Cache()
    #cache.update()
    for package in cache:
        if package.name == deb_name:  
          return clean_apt_versions(package.versions)


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
    myNumber="1.0.0-0"
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
