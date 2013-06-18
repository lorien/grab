# Support raise syntax in Python 2.x
def reraise(tp, value, tb=None):
    raise tp, value, tb
