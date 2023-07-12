
class MockPkgDependency:
    name = ""
    version = ""
    relation = ""
    id = 0
    def __init__(self, name, relation, version, id = 1):
        self.name = name
        self.relation = relation
        self.version = version
        self.id = id
    def __repr__(self):
        return "MockPkgDependency({},{},{},{})".format(self.name, self.relation, self.version, self.id)

class MockOrigin:
    site = ""

class MockAptPkg:
    dependencies = []
    version = ""
    origins = [MockOrigin()]
    uri="artifacts/repository/test"
    def get(self, elem):
        return self

class MockAptInstalledCache:
    installed = {}
    name = ""
    versions = {}
    #installed.dependencies = []
    def __init__(self, name, version, pkg_list):
        self.name = name
        self.installed = MockAptPkg()
        self.installed.dependencies = []
        self.installed.dependencies.extend(pkg_list)
        self.installed.version = version
        self.versions = self.installed

    def is_installed(self):
        return True
    
    def get_installed_cache(self):
        print(self.installed.dependencies)
        return [self]
    def get_cache(self):
        print(self.installed.dependencies)
        return self
    def get(self, name):
        return self

class MockAptCache:
    versions = {}
    installed = {}
    #installed.dependencies = []
    def __init__(self, pkg_list):
        self.versions = pkg_list
        self.installed = MockAptPkg()

    def get_cache(self):
        return self

    def get(self, name):
        return self
    def is_installed(self):
        return True

class MockAptVersion:
    dependencies = []
    version = ""
    def __init__(self, version, pkg_list, name ="python3"):
        self.dependencies = pkg_list
        self.version = version
        self.name = name

    def __repr__(self):
        return "{}{}{}".format(self.name, "=", self.version)