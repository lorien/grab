# coding: utf-8
import setup_script
from grab.spider import Spider, Task
import logging

class TestSpider(Spider):
    def task_generator(self):
        yield Task('initial', url='http://google.com:89/',
                   network_try_count=9)

    def task_initial(self):
        print 'done'


logging.basicConfig(level=logging.DEBUG)
bot = TestSpider(network_try_limit=10)
bot.setup_grab(timeout=1)
bot.run()

