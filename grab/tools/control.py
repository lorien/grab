import time
import logging
from random import randint

logger = logging.getLogger('grab.tools.control')

def sleep(lower_limit, upper_limit):
    """
    Sleep for random number of seconds in interval
    between `lower_limit` and `upper_limit`
    """

    # Doing this math calculations
    # to call randint function with integer arugments
    # There is no random function which accepts float arguments
    lower_limit_float = int(lower_limit * 1000)
    upper_limit_float = int(upper_limit * 1000)
    sleep_time = randint(lower_limit_float, upper_limit_float) / 1000.0
    logger.debug('Sleeping for %f seconds' % sleep_time)
    time.sleep(sleep_time)


def repeat(func, limit=3, args=None, kwargs=None, fatal_exceptions=()):
    for x in xrange(limit):
        ok = False
        try:
            if args is not None and kwargs is not None:
                res = func(*args, **kwargs)
            elif args is not None:
                res = func(*args)
            elif kwargs is not None:
                res = func(**kwargs)
            else:
                res = func()
        except Exception, ex:
            if isinstance(ex, fatal_exceptions):
                raise
            logging.error('', exc_info=ex)
            if x == (limit - 1):
                raise
        else:
            return res
