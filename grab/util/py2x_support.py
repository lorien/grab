"""
    Python 2.x support module
    Usage: from grab.util.py2x_support import *
"""


def reraise(tp, value, tb=None):
    "Support raise syntax in Python 2.x"
    raise tp, value, tb
