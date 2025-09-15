from grab.unset import UNSET


class Data(object):
    """
    Task handlers should return instances of that class.
    """

    def __init__(self, handler_key=None, **kwargs):
        self.handler_key = handler_key
        self.storage = kwargs

    def __getitem__(self, key):
        return self.storage[key]

    def get(self, key, default=UNSET):
        try:
            return self.storage[key]
        except KeyError:
            if default is UNSET:
                raise
            else:
                return default
