"""
Custom exception which Grab instance could generate.

Taxonomy:

Exception
|-> GrabError
    |-> GrabNetworkError <- IOError 
    |-> DataNotFound <- IndexError
    |-> Grab*Error

"""
import warnings


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


class DataNotFound(IndexError, GrabError):
    """
    Indicates that required data is not found.
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


class GrabDeprecationWarning(Warning):
    """
    Raised when some deprecated feature is used.
    """


class GrabInvalidUrl(GrabError):
    """
    Raised when Grab have no idea how to handle the URL or when
    some error occurred while normalizing URL e.g. IDN processing.
    """


def warn(msg):
    warnings.warn(msg, category=GrabDeprecationWarning, stacklevel=3)
