import xml.etree.ElementTree as ET
from os.path import isfile, join
from mobros.constants import CATKIN_BLACKLIST_FILES

def is_catkin_blacklisted(path):
  for black_list_file in CATKIN_BLACKLIST_FILES:
    if isfile( join(path, black_list_file)):
      return True
  return False


class CatkinPackage:
  
  def __init__(self, package_path):
    self.build_dependencies={}
    
    tree = ET.parse(package_path)
    root = tree.getroot()
    self.package_name =root.findall('name')[0].text
    
    self._find_dependencies('build_depend',self.build_dependencies, root)
    self._find_dependencies('depend',self.build_dependencies, root)

  def get_build_deps(self):
    return self.build_dependencies
  
  def get_name(self):
    return self.package_name

  def _find_dependencies(self, dependency_type, dependency_object, xml_root):
    for child in xml_root.findall(dependency_type):
        dependency_name=(child.text).strip()

        if dependency_name not in dependency_object:
          dependency_object[dependency_name]=[]  
        if child.attrib:
          for key in child.attrib.keys():
            dependency_operator=key
            dependency_version=child.attrib[key]

            dependency_object[dependency_name].append({"operator":dependency_operator,"version":dependency_version, "from":self.package_name})


