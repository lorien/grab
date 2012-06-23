#! /usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from grab.spider import Spider, Task
import lxml.html
import random
import os
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('[test memory leaks]')

SCALE = {'kB': 1024.0, 'mB': 1024.0 * 1024.0,
         'KB': 1024.0, 'MB': 1024.0 * 1024.0}

def memory_usage(since=0, render=True):
    """
    Return resident memory usage in bytes.
    """

    proc_status = '/proc/%d/status' % os.getpid()
    try:
        status = open(proc_status).read()
    except:
        return 0
    else:
        line = [x for x in status.splitlines() if 'VmRSS:' in x][0]
        items = line.split('VmRSS:')[1].strip().split(' ')
        mem = float(items[0]) * SCALE[items[1]] - since
        if render:
            metrics = ['b', 'Kb', 'Mb', 'Gb']
            metric = metrics.pop(0)
            for x in xrange(3):
                if mem > 1024:
                    mem = mem / 1024.0
                    metric = metrics.pop(0)
            return '%s %s' % (str(round(mem, 2)), metric)
        else:
            return mem



class TestSpider(Spider):
    initial_urls = ['http://load.local/31m.html']

    def task_initial(self, grab, task):
        logger.debug('Memory usage before %s' % memory_usage())
        #grab.tree.make_links_absolute(grab.response.url)
        #resolved = lxml.html.tostring(grab.tree)
        logger.debug('Memory usage after %s' % memory_usage())


logger.debug('Memory usage before parser start: %s' % memory_usage())
bot = TestSpider()
bot.setup_grab(connect_timeout=30, timeout=180)
bot.run()
logging.debug('Sleeping 3 seconds')
time.sleep(3)
logger.debug('Memory usage before end of script: %s' % memory_usage())
logger.debug('done!')
