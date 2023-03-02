"""Module defining the apt cache singleton not to be constantly requesting apt for his cache"""
import apt
import mobros.utils.logger as logging

# pylint: disable=R0903,W0107
class AptCache:
    """A singleton cache not to be constantly initializing the cache object"""

    cache = apt.Cache()
    try:
        cache.update()
        cache.open()
    except apt.cache.LockFailedException:
        logging.warning(
            "Unable to do apt update. Please run as sudo, or execute it before mobros!"
        )

    def __init__(self):
        """constructor"""
        pass

    def get_cache(self):
        """Singleton get instance of apt cache

        Returns:
            dict: apt cache dict
        """
        return self.cache
