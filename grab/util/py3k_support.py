import sys

# Backward compatibility for xrange function, basestring datatype
# unicode function/type, unichr function and raw_input function
if sys.version_info >= (3, ):
    xrange = range
    basestring = str
    unicode = str
    unichr = chr
    raw_input = input

#from grab.util.py3k_support import *
