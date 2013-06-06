class Data(object):
    """
    Task handlers should return instances of that class.
    You can pass additional parameters in kwargs.

    Examples of usage:
        yield Data('save', data, item_obj=item_obj)
    """

    def __init__(self, name, item, **kwargs):
        self.name = name
        self.item = item

        for key, value in kwargs.items():
            setattr(self, key, value)


    def __getitem__(self, key):
        return getattr(self, key, None)
