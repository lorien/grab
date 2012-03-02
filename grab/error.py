"""
Custom exception which could generate Grab instance.
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
    """


class DataNotFound(IndexError, GrabError):
    """
    Indictes that required data is not found.
    """


class GrabMisuseError(GrabError):
    """
    Indicates incorrect usage of grab API.
    """
