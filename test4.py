#! /usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from lxml.html import fromstring
import os
from grab.tools.memory import memory_usage
import time
from pympler import muppy, summary
from lxml import etree
import threading

#import pdb; pdb.set_trace()
#etree.use_global_python_log(etree.PyErrorLog('WARNING'))

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('[test memory leaks]')

def func():
    def worker():
        tree = fromstring(open('/web/load/31m.html').read())
        print tree.xpath('//title')[0].text
        del tree

    t = threading.Thread(target=worker)
    t.start()
    t.join()

logger.debug('Memory usage before build tree: %s' % memory_usage())
func()
logger.debug('Memory usage after building the tree: %s' % memory_usage())
time.sleep(2)
logger.debug('Memory usage after deleting the tree: %s' % memory_usage())
