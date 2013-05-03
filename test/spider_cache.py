from unittest import TestCase
import pymongo

from grab.spider import Spider, Task
from .tornado_util import SERVER

db = pymongo.Connection()['spider_test']

class SimpleSpider(Spider):
    def task_foo(self, grab, task):
        grab.setup(url=SERVER.BASE_URL)
        yield Task('bar', grab=grab)

    def task_bar(self, grab, task):
        pass


class TestSpiderCache(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_bug1(self):
        """
        Test the bug:
        * enable cache
        * fetch document (it goes to cache)
        * request same URL
        * got exception
        """

        db.cache.remove({})
        bot = SimpleSpider()
        bot.setup_cache(backend='mongo', database='spider_test')
        bot.setup_queue()
        bot.add_task(Task('foo', SERVER.BASE_URL))
        bot.run()
