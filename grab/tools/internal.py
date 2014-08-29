import warnings
from functools import wraps
import logging
#from grab.error import GrabMisuseError


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
            #warnings.warn(message, category=GrabMisuseError, stacklevel=2)
            logging.error(message)
            return func(*args, **kwargs)
        return new_func
    return wrapped
