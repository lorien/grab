import warnings
import logging
import traceback
import sys

DISABLE_WARNINGS = False


class GrabDeprecationWarning(UserWarning):
    """
    Warning category used in Grab to generate
    warning messages.
    """


def warn(msg, stacklevel=2):
    warnings.warn(msg, category=GrabDeprecationWarning, stacklevel=stacklevel)
    frame = sys._getframe()  # pylint: disable=protected-access
    logging.debug(
        "Deprecation Warning\n%s", "".join(traceback.format_stack(f=frame.f_back))
    )
