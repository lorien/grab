import time
import logging
from random import randint

from grab.util.py3k_support import *

logger = logging.getLogger('grab.tools.control')


def sleep(lower_limit, upper_limit):
    """
    Sleep for random number of seconds in interval
    between `lower_limit` and `upper_limit`
    """

    # Doing this math calculations
    # to call randint function with integer arguments
    # There is no random function which accepts float arguments
    lower_limit_float = int(lower_limit * 1000)
    upper_limit_float = int(upper_limit * 1000)
    sleep_time = randint(lower_limit_float, upper_limit_float) / 1000.0
    logger.debug('Sleeping for %f seconds' % sleep_time)
    time.sleep(sleep_time)


def repeat(func, limit=3, args=None, kwargs=None,
           fatal_exceptions=(), valid_exceptions=()):
    """
    Return value of execution `func` function.

    In case of error try to execute `func` maximum `limit` times
    and then raise latest exception.

    Example::

        def download(url):
            return urllib.urlopen(url).read()

        data = repeat(download, 3, args=['http://google.com/'])

    """
    for try_count in xrange(1, limit + 1):
        try:
            res = func(*(args or ()), **(kwargs or {}))
        except Exception as ex:
            if isinstance(ex, fatal_exceptions):
                raise
            elif valid_exceptions and not isinstance(ex, valid_exceptions):
                raise
            else:
                logging.error('', exc_info=ex)
                if try_count >= limit:
                    logger.error('Too many errors while executing function %s' % func.__name__)
                    raise
        else:
            return res
