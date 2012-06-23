#! /usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from grab.spider import Spider, Task
import lxml.html
import random
import os
import time
from grab.tools.memory import memory_usage

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('[test memory leaks]')

CACHE = []

class TestSpider(Spider):
    initial_urls = ['http://load.local/31m.html']

    def task_initial(self, grab, task):
        logger.debug('Memory usage before %s' % memory_usage())
        #grab.tree.make_links_absolute(grab.response.url)
        #resolved = lxml.html.tostring(grab.tree)
        CACHE.append(grab.response.body)
        logger.debug('Memory usage after %s' % memory_usage())

    def shutdown(self):
        logger.debug('Memory usage in spider shutdown: %s' % memory_usage())

logger.debug('Memory usage before parser start: %s' % memory_usage())
bot = TestSpider()
bot.setup_grab(connect_timeout=30, timeout=180)
bot.run()
logging.debug('Sleeping 3 seconds')
time.sleep(1)
logger.debug('Memory usage after spider: %s' % memory_usage())

tree = lxml.html.fromstring(CACHE[0])
logger.debug('Memory usage after fromstring: %s' % memory_usage())
del tree
time.sleep(3)
logger.debug('Memory usage after delete tree: %s' % memory_usage())

logger.debug('done!')
