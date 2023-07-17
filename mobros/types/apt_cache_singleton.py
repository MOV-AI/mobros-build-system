"""Module defining the apt cache singleton not to be constantly requesting apt for his cache"""
import os
import apt

import mobros.utils.logger as logging
from mobros.exceptions import AptCacheInitializationException
from mobros.utils.utilitary import execute_shell_command


# pylint: disable=R0903,W0107
class AptCache:
    """Apt cache singleton"""

    _instance = None
    _cache = None
    _installed_cache = None

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
            except apt.cache.FetchFailedException as fetched_failed_exception:
                logging.error(str(fetched_failed_exception))
                message = "Unable to fetch apt cache. Please check your internet connection! Try running 'sudo apt update' for more info."
                logging.error(message)

                apt_cmd = ["apt", "update"]
                if os.geteuid() != 0:
                    apt_cmd = ["sudo"] + apt_cmd
                execute_shell_command(apt_cmd, log_output=True)
                raise AptCacheInitializationException(message) from fetched_failed_exception

            cls._installed_cache = []
            for cached_pkg in cls._cache: # pylint: disable=not-an-iterable
                if cached_pkg.is_installed:
                    cls._installed_cache.append(cached_pkg)

        return cls._instance

    def get_cache(self):
        """Singleton get instance of apt cache

        Returns:
            dict: apt cache dict
        """
        return self._cache

    def get_installed_cache(self):
        """Getter function to get the cache installed only"""
        return self._installed_cache
