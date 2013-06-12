import sys

# Backward compatibility for xrange function,
# basestring datatype and unicode function/type
if sys.version_info >= (3,):
    xrange = range
    basestring = str
    unicode = str

#from grab.util import py3k_support
