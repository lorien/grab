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
        url_template = 'http://load.local/grab%d.html'
        #fast_url = 'http://load.local/grab0.html'
        slow_url = 'http://load.local/slow.html'
        #yield Task('load', url=slow_url, disable_cache=True)
        #yield Task('load', url=fast_url, disable_cache=False)
        for x in xrange(500):
            disable_flag = True#not (x % 2)
            yield Task('load', url=url_template % x, disable_cache=disable_flag)
            #if randint(0, 10) == 10:
                #yield Task('load', url=slow_url, disable_cache=True)

    def task_load(self, grab, task):
        assert 'grab' in grab.response.body
        print('ok', task.url)


@timer
def main():
    default_logging()
    bot = SpeedSpider(thread_number=30)
    bot.setup_cache(database='speed_spider', use_compression=True)
    bot.run()
    print(bot.render_stats())

if __name__ == '__main__':
    main()
