#!/usr/bin/env python
# coding: utf-8
import csv
import logging

from grab.spider import Spider, Task
from grab import Grab

logging.basicConfig(level=logging.DEBUG)

def main():
    for x in xrange(1):
        g = Grab()
        #g.setup(body_maxsize=8 * 1024 * 1024)
        g.go('http://load.local/31m.html')
        #g.go('http://bombaybazaar.se/henna.php?page=8927')
        print len(g.response.body)


main()
