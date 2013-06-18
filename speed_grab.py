#!/usr/bin/env python
# coding: utf-8
from grab import Grab
from grab.tools.work import make_work
from grab.tools.logs import default_logging
import time
import logging
#import urllib

from grab.util.py3k_support import *

#logging.basicConfig(level=logging.DEBUG)

def timer(func):
    """
    Display time taken to execute the decorated function.
    """

    def inner(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        total = time.time() - start
        print('Time: %.2f sec.' % total)
        return result
    return inner


@timer
def main():
    default_logging()
    for x in xrange(500):
        url = 'http://load.local/grab.html'
        g = Grab()
        g.go(url)
        assert 'grab' in g.response.body
        #g.tree
        #urllib.urlopen(url).read()

if __name__ == '__main__':
    main()
