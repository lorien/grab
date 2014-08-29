"""
    Python 2.x (older than 2.6) support module
    Usage: from grab.util.py2old_support import *
"""

import sys

# Support next function for Python older than 2.6
if sys.version_info < (2, 6):
    def next(it):
        return it.next()
