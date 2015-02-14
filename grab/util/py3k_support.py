"""
    Python 3.x support module
    Usage: from grab.util.py3k_support import *
"""

import sys

PY3K = (sys.version_info >= (3, ))

# Backward compatibility for xrange function, basestring datatype
# unicode function/type, unichr function and raw_input function
if PY3K:
    xrange = range
    basestring = str
    unicode = str
    unichr = chr
    raw_input = input
