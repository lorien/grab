"""
Custom exception which Grab instance could generate.

Taxonomy:

Exception
|-> GrabError
    |-> GrabNetworkError
        |-> GrabTimeoutError
        |-> GrabConnectionError
        |-> GrabCouldNotResolveHostError
    |-> GrabAuthError
    |-> GrabMisuseError
    |-> GrabTooManyRedirectsError
    |-> GrabInvalidUrl
    |-> GrabInternalError

Exception
| -> weblib.error.WeblibError
     |-> DataNotFound <- IndexError
"""

from __future__ import absolute_import
from weblib.error import DataNotFound  # noqa pylint: disable=unused-import


class GrabError(Exception):
    """
    All custom Grab exception should be children of that class.
    """


class GrabNetworkError(GrabError):
    """
    Raises in case of network error.
    """

    def __init__(self, *args, **kwargs):
        if len(args) > 1:
            self.original_exc = args[1]
        else:
            self.original_exc = None
        super(GrabNetworkError, self).__init__(*args, **kwargs)


class GrabTimeoutError(GrabNetworkError):
    """
    Raises when configured time is outed for the request.

    In curl transport it is CURLE_OPERATION_TIMEDOUT (28)
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


class GrabMisuseError(GrabError):
    """
    Indicates incorrect usage of grab API.
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
