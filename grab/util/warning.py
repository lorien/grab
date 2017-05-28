import warnings
from functools import wraps
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
    frame = sys._getframe() # pylint: disable=protected-access
    logging.debug('Deprecation Warning\n' +
                  ''.join(traceback.format_stack(f=frame.f_back)))


# from https://github.com/scrapy/scrapy/blob/master/scrapy/utils/decorator.py
def deprecated(use_instead=None):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used."""

    def wrapped(func):
        @wraps(func)
        def new_func(*args, **kwargs):
            message = "Call to deprecated function %s." % func.__name__
            if use_instead:
                message += " Use %s instead." % use_instead
            if not DISABLE_WARNINGS:
                warn(message, stacklevel=3)
            return func(*args, **kwargs)
        return new_func
    return wrapped
