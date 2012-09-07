#!/usr/bin/env python
# coding: utf-8
import logging
import signal

from grab import Grab
from grab.error import GrabNetworkError
from grab.tools.watch import watch

logging.basicConfig(level=logging.DEBUG)

def handler(signum, frame):
    print 'Got SIGUSR2'


def main():
    signal.signal(signal.SIGUSR2, handler)

    for x in xrange(1000):
        g = Grab()
        try:
            g.go('http://ya.ru')
        except GrabNetworkError, ex:
            logging.error('', exc_info=ex)


if __name__ == '__main__':
    #watch()
    main()
