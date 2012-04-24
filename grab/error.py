"""
Custom exception which could generate Grab instance.

Taxonomy:

Exception
|-> GrabError
    |-> GrabNetworkError <- IOError 
    |-> DataNotFound <- IndexError
    |-> Grab*Error

"""

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
    Indictes that required data is not found.
    """


class GrabMisuseError(GrabError):
    """
    Indicates incorrect usage of grab API.
    """


class GrabConnectionError(GrabError):
    """
    Raised then it is not possible to establish network connection.

    In curl transport it is CURLE_COULDNT_CONNECT (7)
    """

class GrabAuthError(GrabError):
    """
    Raised then remote server denies authentication credentials.

    In curl transport it is CURLE_COULDNT_CONNECT (67)
    """
