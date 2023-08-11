"""Module defining the apt cache singleton not to be constantly requesting apt for his cache"""
import os
from time import sleep
import apt

import mobros.utils.logger as logging
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

            attempt = 0
            max_attempts = 5
            while attempt < max_attempts:
                try:
                    cls._cache.update()
                    cls._cache.open()
                    break
                except apt.cache.LockFailedException:
                    logging.warning(
                        "Unable to do apt update. Please run as sudo, or execute it before mobros!"
                    )
                except apt.cache.FetchFailedException:
                    logging.warning("Unable to fetch apt cache. Please check your internet connection!")

                attempt += 1
                logging.warning("Trying again in 15 seconds (" + str(attempt) +  " of " + str(max_attempts) + ") ...")
                sleep(5)

            if attempt == max_attempts:
                apt_cmd = ["apt", "update"]
                if os.geteuid() != 0:
                    apt_cmd = ["sudo"] + apt_cmd
                execute_shell_command(apt_cmd, log_output=True)

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
