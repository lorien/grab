#!/usr/bin/env python
import time
from grab import Grab
from grab.spider import Spider, Task
import logging
import itertools

from test.server import SERVER, start_server, stop_server

def timeout_iterator():
    timeouts = [0]#(0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1)
    for tm in itertools.cycle(timeouts):
        yield tm


class TestSpider(Spider):
    def task_generator(self):
        for x in range(1000):
            yield Task('page', url=SERVER.BASE_URL)

    def task_page(self, grab, task):
        assert grab.doc.body == b'foo'


def main():
    start_server()

    SERVER.TIMEOUT_ITERATOR = timeout_iterator()
    SERVER.RESPONSE['get'] = 'foo'

    bot = TestSpider(thread_number=1000)
    bot.run()
    print(bot.render_stats())

    stop_server()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
