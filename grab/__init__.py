from base import (GrabError, DataNotFound, GrabNetworkError,
                  GrabMisuseError, UploadContent, UploadFile,
                  GrabTimeoutError)
from transport.curl import GrabCurl
#from transport.urllib import GrabUrllib
from transport.selenium import GrabSelenium
from transport.requests import GrabRequests

Grab = GrabCurl

version_info = (0, 3, 16)
__version__ = '.'.join(map(str, version_info))
