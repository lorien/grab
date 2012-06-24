#!/usr/bin/env python
# coding: utf-8
from grab.spider import Spider, Task
from grab.tools.logs import default_logging
import time
import logging

URL_28K = 'http://load.local/28k.html'

def timer(func):
    """
    Display time taken to execute the decorated function.
    """

    def inner(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        total = time.time() - start
        print 'Time: %.2f sec.' % total
        return result
    return inner


class SpeedSpider(Spider):
    def task_generator(self):
        for x in xrange(500):
            yield Task('load', url=URL_28K)

    def task_load(self, grab, task):
        assert 'Scrapy' in grab.response.body


@timer
def main():
    default_logging()
    bot = SpeedSpider(thread_number=30)
    bot.run()
    print bot.render_stats()

if __name__ == '__main__':
    main()
