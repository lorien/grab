#!/usr/bin/env python
# coding: utf-8
from grab.spider import Spider, Task
from grab.tools.logs import default_logging
import time
import logging

URL_28K = 'http://load.local/grab.html'

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
        url_template = 'http://load.local/grab%d.html'
        for x in xrange(1000):
            disable_flag = not (x % 2)
            yield Task('load', url=url_template % x, disable_cache=disable_flag)

    def task_load(self, grab, task):
        assert 'grab' in grab.response.body


@timer
def main():
    default_logging()
    bot = SpeedSpider(thread_number=30)
    bot.setup_cache(database='speed_spider', use_compression=True)
    bot.run()
    print bot.render_stats()

if __name__ == '__main__':
    main()
