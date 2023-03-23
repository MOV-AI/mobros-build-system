"""Module defining the apt cache singleton not to be constantly requesting apt for his cache"""
import apt
import mobros.utils.logger as logging

# pylint: disable=R0903,W0107
class AptCache():
    """Apt cache singleton"""
    _instance = None
    _cache = None

    def __new__(cls):
        """Singleton lock of instance"""
        if cls._instance is None:
            cls._instance = super(AptCache, cls).__new__(cls)
            cls._cache = apt.Cache()

            try:
                cls._cache.update()
                cls._cache.open()
            except apt.cache.LockFailedException:
                logging.warning(
                    "Unable to do apt update. Please run as sudo, or execute it before mobros!"
                )

        return cls._instance

    def get_cache(self):
        """Singleton get instance of apt cache

        Returns:
            dict: apt cache dict
        """
        return self._cache
