import abc

class BaseBackend(object):
    __metaclass__  = abc.ABCMeta

    @staticmethod
    def getBackend(argv, config):
        # When we support multiple backends, this needs to be changed.
        backend_type = config['backend_default']['type']
        backend = __import__("backends." + backend_type)

        types = BaseBackend.__subclasses__()
        backend = types.pop()

        return backend(config['backend_default'])

    # Return a list of TimeEntry objects.
    @abc.abstractmethod
    def getTimeEntries(self, from_date, to_date = None):
         return []

    @abc.abstractmethod
    def __init__(self, config):
        return
