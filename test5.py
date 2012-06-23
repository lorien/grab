#! /usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import time

from grab.error import GrabNetworkError, GrabTimeoutError
from grab.spider import Spider, Task

import lxml.html
import random

logging.basicConfig(
    level=logging.DEBUG,
)
logger = logging.getLogger('[test memory leaks]')
import os
import pdb

_proc_status = '/proc/%d/status' % os.getpid()

_scale = {'kB': 1024.0, 'mB': 1024.0 * 1024.0,
          'KB': 1024.0, 'MB': 1024.0 * 1024.0}

def _VmB(VmKey):
    '''Private.
    '''
    global _proc_status, _scale
    # get pseudo file  /proc/<pid>/status
    try:
        t = open(_proc_status)
        v = t.read()
        t.close()
    except:
        return 0.0  # non-Linux?
        # get VmKey line e.g. 'VmRSS:  9999  kB\n ...'
    i = v.index(VmKey)
    v = v[i:].split(None, 3)  # whitespace
    if len(v) < 3:
        return 0.0  # invalid format?
        # convert Vm value to bytes
    return float(v[1]) * _scale[v[2]]


def resident(since=0.0):
    '''Return resident memory usage in bytes.
    '''
    return _VmB('VmRSS:') - since

THREADS = 4

class HTTPOKSpider(Spider):
    """
    initial_urls - пачка урлов, ниже приведен для примера
    """
    count = 0
    initial_urls = ['http://load.local/31m.html'] * 200

    def task_initial(self, grab, task):
        self.count = self.count + 1
        m = int(resident() / 1024 / 1024)
        logger.debug('Memory usage before %s MB, number of url %s' % (m, self.count))
        logger.debug('%s taskq size' % self.taskq.size())
        #pdb.set_trace()

        #body = lxml.html.fromstring(grab.response.unicode_body())
        #body.make_links_absolute(grab.response.url)
        #resolved = lxml.html.tostring(body)

        #grab.tree.make_links_absolute(grab.response.url)
        #resolved = lxml.html.tostring(grab.tree)
        m = int(resident() / 1024 / 1024)
        logger.debug('Memory usage after %s MB, number of url %s' % (m, self.count))
        logger.debug('#############')


bot = HTTPOKSpider(
    thread_number=THREADS,
    network_try_limit=1,
    task_try_limit=1,
)
#body_maxsize = int(10 * 1024 * 1024)
bot.setup_grab(method='GET', connect_timeout=30, timeout=180)
bot.run()
m = int(resident() / 1024 / 1024)
# destroy!!!!
del bot
time.sleep(2)
logger.debug('Memory usage before end of script %s MM' % m)
logger.debug('done!')
