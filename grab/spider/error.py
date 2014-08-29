__all__ = ('SpiderError', 'SpiderMisuseError', 'FatalError',
           'StopTaskProcessing', 'SpiderInternalError',
           'NoTaskHandler', 'NoDataHandler')


class SpiderError(Exception):
    """Base class for Spider exceptions"""


class SpiderMisuseError(SpiderError):
    """Improper usage of Spider framework"""


class FatalError(SpiderError):
    """Fatal error which should stop parsing process"""


class StopTaskProcessing(SpiderError):
    """
    Used in middlewares to stop task processing
    """


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
