"""
Custom exception which could generate Grab instance.
"""

class GrabError(Exception):
    """
    All custom Grab exception should be children of that class.
    """

class GrabNetworkError(IOError, GrabError):
    """
    Wrapper about pycurl error.
    """


class DataNotFound(IndexError, GrabError):
    """
    Indictes that required data is not found.
    """


class GrabMisuseError(GrabError):
    """
    Indicates incorrect usage of grab API.
    """


class GrabTimeoutError(GrabNetworkError):
    """
    Raised when time is outed for request.
    """
