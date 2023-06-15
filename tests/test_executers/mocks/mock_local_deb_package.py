
class DebPackage:
    def __init__(self, package_name, version="0.0.0.0"):
        self._sections={}
        self._sections["Package"] = package_name
        self._sections["Version"] = version
        self._sections["Depends"] = []
        self._sections["Pre-Depends"] = []
        self.depends = ""
