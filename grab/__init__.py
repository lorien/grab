from base import (GrabError, DataNotFound, GrabNetworkError,
                  GrabMisuseError, UploadContent, UploadFile)
from transport.curl import GrabCurl
#from transport.urllib import GrabUrllib
from transport.splinter import GrabSplinter
from transport.requests import GrabRequests

Grab = GrabCurl

version_info = (0, 3, 14)
__version__ = '.'.join(map(str, version_info))
