# import logging
# import sys
# import traceback
import warnings

# See tests.ext_lxml
# DISABLE_WARNINGS = False


class GrabDeprecationWarning(UserWarning):
    """Warning category used in Grab to generate warning messages."""


def warn(msg: str, stacklevel: int = 2) -> None:
    warnings.warn(msg, category=GrabDeprecationWarning, stacklevel=stacklevel)
    # frame = sys._getframe()  # pylint: disable=protected-access
    # logging.debug(
    #    "Deprecation Warning\n%s", "".join(traceback.format_stack(f=frame.f_back))
    # )
