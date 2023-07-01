"""Custom exception which Grab instance could generate.

## Exceptions

- GrabError
    - GrabNetworkError
        - GrabTimeoutError
        - GrabConnectionError
        - GrabCouldNotResolveHostError
    - GrabAuthError
    - GrabMisuseError
    - GrabTooManyRedirectsError
    - GrabInvalidUrl
    - GrabInternalError
    - GrabFeatureIsDeprecated
    - ResponseNotValid
- DataNotFound == IndexError

## Warnings

- GrabDeprecationWarning

"""
from typing import Any


class GrabError(Exception):
    """All custom Grab exception should be children of that class."""


class OriginalExceptionGrabError(GrabError):
    """Sub-class which constructor accepts original exception as second argument."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if len(args) > 1:
            self.original_exc = args[1]
        else:
            self.original_exc = None
        super().__init__(*args, **kwargs)


class GrabNetworkError(OriginalExceptionGrabError):
    """Raises in case of network error."""


class GrabTimeoutError(GrabNetworkError):
    """Raises when configured time is outed for the request."""


class GrabConnectionError(GrabNetworkError):
    """Raised when it is not possible to establish network connection."""


class GrabCouldNotResolveHostError(GrabNetworkError):
    """Raised when couldn't resolve host. The given remote host was not resolved."""


class GrabAuthError(GrabError):
    """Raised when remote server denies authentication credentials."""


class GrabMisuseError(GrabError):
    """Indicates incorrect usage of grab API."""


class GrabTooManyRedirectsError(GrabError):
    """Raised when max. allowed number of redirects is reaced."""


class GrabInvalidUrlError(GrabError):
    """Raised when error occurred while normalizing URL e.g. IDN processing."""


class GrabInvalidResponseError(OriginalExceptionGrabError):
    """Raised when network response's data could not be processed."""


class GrabInternalError(OriginalExceptionGrabError):
    pass


class GrabFeatureIsDeprecatedError(GrabError):
    """Raised when user tries to use feature that is deprecated and has been dropped."""


def raise_feature_is_deprecated(feature_name: str) -> None:
    raise GrabFeatureIsDeprecatedError(
        "{} is deprecated and have been disabled".format(feature_name)
    )


# @date: Dec 08, 2022
# @comment:
# Previously DataNotFound (sublass of IndexError) exception were in weblib package.
# I am moving away from using weblib package.
# To minimize failures in external code which uses DataNotFound class I make
# it alias of IndexError
DataNotFound = IndexError


class ResponseNotValidError(GrabError):
    pass


class GrabDeprecationWarning(UserWarning):
    pass
