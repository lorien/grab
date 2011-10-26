#!/usr/bin/env python
# coding: utf-8
from grab import Grab, make_work
import time
import logging
import urllib

#logging.basicConfig(level=logging.DEBUG)

def timer(func):
    """
    Display time taken to execute the decorated function.
    """

    def inner(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        total = time.time() - start
        print 'Time: %.2f sec.' % total
        return result
    return inner


@timer
def main():
    for x in xrange(100):
        url = 'http://load.local/28k.html'
        g = Grab()
        g.go(url)
        #urllib.urlopen(url).read()

if __name__ == '__main__':
    main()
