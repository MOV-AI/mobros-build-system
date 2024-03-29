"""Module defining the global data singleton to share data between modules"""

# pylint: disable=R0903,W0107
class GlobalData:
    """Mobros shared data singleton"""

    _instance = None
    _pkg_list = {}
    _pkg_source_blacklist_patterns = []

    def __new__(cls):
        """Singleton lock of instance"""
        if cls._instance is None:
            cls._instance = super(GlobalData, cls).__new__(cls)

        return cls._instance

    def set_user_package(self, package_name, version):
        """Set user package list
        """

        self._pkg_list[package_name] = version

    def get_user_pkg_list(self):
        """Get list of user inputed packages

        Returns:
            dict: user input package dict
        """
        return self._pkg_list

    def is_package_user_requested(self, package_name):
        """Singleton get instance of the gobal data

        Returns:
            dict: apt cache dict
        """
        return package_name in self._pkg_list

    def set_conflict_solving_blacklist(self, blacklist_patterns):
        """Set the blacklist patterns for mobros auto conflict solving

        """

        self._pkg_source_blacklist_patterns = blacklist_patterns

    def get_conflict_solving_blacklist(self):
        """Get the blacklist patterns for mobros auto conflict solving

        Returns:
            list: package source blacklist patterns
        """
        return self._pkg_source_blacklist_patterns
