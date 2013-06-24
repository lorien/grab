class Data(object):
    """
    Task handlers should return instances of that class.
    """

    def __init__(self, data_name, **kwargs):
        self.name = data_name
        self.storage = kwargs
