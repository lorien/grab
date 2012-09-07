#!/usr/bin/env python
# coding: utf-8
import logging
import signal

from grab import Grab
from grab.spider import Spider, Task
from grab.error import GrabNetworkError
from grab.tools.watch import watch

logging.basicConfig(level=logging.DEBUG)

def handler(signum, frame):
    print 'Got SIGUSR2'


class TestSpider(Spider):
    def task_generator(self):
        for x in xrange(1000):
            yield Task('foo', url='http://google.com')

    def task_foo(self, grab, task):
        print task.url


def main():
    bot = TestSpider(thread_number=20)
    bot.run()


if __name__ == '__main__':
    #watch()
    main()
