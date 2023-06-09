
class MockPkgDependency:
    name = ""
    version = ""
    relation = ""
    def __init__(self, name, relation, version):
        self.name = name
        self.relation = relation
        self.version = version

    def __repr__(self):
        return "MockPkgDependency({},{},{})".format(self.name, self.relation, self.version)

class MockAptPkg:
    dependencies = []
    version = ""

class MockAptCache:
    installed = MockAptPkg()
    name = ""
    #installed.dependencies = []
    def __init__(self, name, version, pkg_list):
        self.name = name
        
        self.installed.dependencies.extend(pkg_list)
        self.installed.version = version
    def is_installed(self):
        return True
    
    def get_installed_cache(self):
        return [self]
