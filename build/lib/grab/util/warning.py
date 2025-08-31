import warnings

# See tests.ext_lxml
# DISABLE_WARNINGS = False


class GrabDeprecationWarning(UserWarning):
    """Warning category used in Grab to generate warning messages."""


def warn(msg: str, stacklevel: int = 2) -> None:
    warnings.warn(msg, category=GrabDeprecationWarning, stacklevel=stacklevel)
