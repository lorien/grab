#!/usr/bin/env python
# coding: utf-8
from grab.spider import Spider, Task
from grab.tools.logs import default_logging
import time
import logging
from random import randint

from grab.util.py3k_support import *

URL_28K = 'http://load.local/grab.html'

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


class SpeedSpider(Spider):
    def task_generator(self):
        url = 'http://load.local/grab.html'
        for x in xrange(500):
            yield Task('load', url=url)

    def task_load(self, grab, task):
        assert 'grab' in grab.response.body
        print('ok', task.url)


@timer
def main():
    default_logging()
    bot = SpeedSpider(thread_number=30)
    bot.run()
    print(bot.render_stats())

if __name__ == '__main__':
    main()
