"""
    Python 2.x support module
    Usage: from grab.util.py2x_support import *
"""


# Support raise syntax in Python 2.x
def reraise(tp, value, tb=None):
    raise tp, value, tb
