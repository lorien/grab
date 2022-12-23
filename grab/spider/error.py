from grab.errors import GrabError

__all__ = (
    "SpiderError",
    "SpiderMisuseError",
    "FatalError",
    "SpiderInternalError",
    "NoTaskHandler",
    "NoDataHandler",
)


class SpiderError(GrabError):
    """Base class for Spider exceptions."""


class SpiderConfigurationError(SpiderError):
    pass


class SpiderMisuseError(SpiderError):
    """Improper usage of Spider framework."""


class FatalError(SpiderError):
    """Fatal error which should stop parsing process."""


class SpiderInternalError(SpiderError):
    """Raises when error throwned by internal spider logic.

    Like spider class discovering, CLI error.
    """


class NoTaskHandler(SpiderError):
    """Raise when no handler found to process network response."""


class NoDataHandler(SpiderError):
    """Raise when no handler found to process Data object."""
