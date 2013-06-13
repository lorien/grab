import sys

# Backward compatibility for xrange function, basestring datatype
# unicode function/type and unichr function
if sys.version_info >= (3,):
    xrange = range
    basestring = str
    unicode = str
    unichr = chr

#from grab.util import py3k_support
