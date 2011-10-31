from base import (GrabError, DataNotFound, GrabNetworkError,
                  GrabMisuseError, UploadContent, UploadFile)
from transport.curl import GrabCurl
#from transport.urllib import GrabUrllib

Grab = GrabCurl
