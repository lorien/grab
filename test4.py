#! /usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from lxml.html import fromstring
import os
from grab.tools.memory import memory_usage
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('[test memory leaks]')

def func():
    tree = fromstring(open('/web/load/31m.html').read())

logger.debug('Memory usage before build tree: %s' % memory_usage())
func()
logger.debug('Memory usage after building the tree: %s' % memory_usage())
time.sleep(2)
logger.debug('Memory usage after deleting the tree: %s' % memory_usage())
