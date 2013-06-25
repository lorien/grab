NULL = object()

class Data(object):
    """
    Task handlers should return instances of that class.
    """

    def __init__(self, data_name, **kwargs):
        self.data_name = data_name
        self.storage = kwargs

    def __getitem__(self, key):
        return self.storage[key]

    def get(self, key, default=NULL):
        try:
            return self.storage[key]
        except KeyError:
            if default is NULL:
                raise
            else:
                return default
