#!/usr/bin/env python
# coding: utf-8
import csv
import logging
import signal
import time

from grab.spider import Spider, Task
from grab import Grab
from grab.error import GrabNetworkError
from grab.tools.watch import watch

logging.basicConfig(level=logging.DEBUG)

def handler(signum, frame):
    print 'Got SIGUSR2'


def main():
    signal.signal(signal.SIGUSR2, handler)

    start = time.time()
    for x in xrange(100):
        g = Grab()
        try:
            g.go('http://load.local/grab.html')
            g.tree
        except GrabNetworkError, ex:
            logging.error('', exc_info=ex)
        print len(g.response.body)
    stop = time.time()
    print '%.2f' % (stop - start)


if __name__ == '__main__':
    watch()
    main()
