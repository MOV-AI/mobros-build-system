"""Module that offers all costume exceptions raised by this package"""


class InstallCandidateNotFoundException(Exception):
    """Exception when there is no suitable candidate found"""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ColisionDetectedException(Exception):
    """Exception when there is a colision between rules"""

    def __init__(self, conflict):
        super().__init__()
        self.conflict = conflict

    def get_conflicts(self):
        """Get the conflicts stored within the exception

        Returns:
            conflict: conflict object with all conflict information
        """
        return self.conflict

class AptCacheInitializationException(Exception):
    """Exception when host's apt cache is not initialized successfully"""

    def __init__(self, message):
        super().__init__(message)
        self.message = message
