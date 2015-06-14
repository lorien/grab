from __future__ import absolute_import
from grab.error import GrabError


__all__ = ('SpiderError', 'SpiderMisuseError', 'FatalError',
           'SpiderInternalError',
           'NoTaskHandler', 'NoDataHandler')


class SpiderError(GrabError):
    """Base class for Spider exceptions"""


class SpiderConfigurationError(SpiderError):
    pass


class SpiderMisuseError(SpiderError):
    """Improper usage of Spider framework"""


class FatalError(SpiderError):
    """Fatal error which should stop parsing process"""


class SpiderInternalError(SpiderError):
    """
    Used to indicate error in some internal spider services
    like spider class discovering, CLI error
    """


class NoTaskHandler(SpiderError):
    """
    Used then it is not possible to find which
    handler should be used to process network response.
    """


class NoDataHandler(SpiderError):
    """
    Used then it is not possible to find which
    handler should be used to process Data object.
    """
