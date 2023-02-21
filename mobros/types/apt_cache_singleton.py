import apt 
import mobros.utils.logger as logging
class AptCache():
    """A singleton cache not to be constantly initializing the cache object
    """
    cache = apt.Cache()
    try:
        # duarte broknen apt
        #cache.update()
        cache.open()
    except apt.cache.LockFailedException:
        logging.warning(
            "Unable to do apt update. Please run as sudo, or execute it before mobros!"
        )

    def __init__(self):
        pass

    def get_cache(self):
        return self.cache