"""Module that offers all costume exceptions raised by this package"""


class InstallCandidateNotFoundException(Exception):
    """Exception when there is no suitable candidate found"""

    def __init__(self, message):
        super().__init__(message)
        self.message = message

class ColisionDetectedException(Exception):
    """Exception when there is a colision between rules"""

    def __init__(self, message):
        super().__init__(message)
        self.message = message