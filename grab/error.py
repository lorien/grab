from __future__ import absolute_import
"""
Custom exception which Grab instance could generate.

Taxonomy:

Exception
|-> GrabError
    |-> GrabNetworkError <- IOError
    |-> Grab*Error

Exception
| -> weblib.error.WeblibError
     |-> DataNotFound <- IndexError
"""
from weblib.error import DataNotFound  # noqa


class GrabError(Exception):
    """
    All custom Grab exception should be children of that class.
    """


class GrabNetworkError(IOError, GrabError):
    """
    Raises in case of network error.
    """


class GrabTimeoutError(GrabNetworkError):
    """
    Raises when configured time is outed for the request.

    In curl transport it is CURLE_OPERATION_TIMEDOUT (28)
    """


class GrabMisuseError(GrabError):
    """
    Indicates incorrect usage of grab API.
    """


class GrabConnectionError(GrabNetworkError):
    """
    Raised when it is not possible to establish network connection.

    In curl transport it is CURLE_COULDNT_CONNECT (7)
    """


class GrabCouldNotResolveHostError(GrabNetworkError):
    """
    URLE_COULDNT_RESOLVE_HOST (6)
    Couldn't resolve host. The given remote host was not resolved.
    """


class GrabAuthError(GrabError):
    """
    Raised when remote server denies authentication credentials.

    In curl transport it is CURLE_COULDNT_CONNECT (67)
    """


class GrabTooManyRedirectsError(GrabError):
    """
    Raised when Grab reached max. allowd number of redirects for
    one request.
    """


class GrabInvalidUrl(GrabError):
    """
    Raised when Grab have no idea how to handle the URL or when
    some error occurred while normalizing URL e.g. IDN processing.
    """


class GrabInternalError(GrabError):
    pass
