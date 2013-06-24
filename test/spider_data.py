from unittest import TestCase

from grab import Grab
from grab.spider import Spider, Task, Data, NoDataHandler, SpiderMisuseError

from .tornado_util import SERVER

class TestSpider(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_data_nohandler_error(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                yield Data('foo', 1)

        bot = TestSpider()
        bot.setup_queue()
        bot.add_task(Task('page', url=SERVER.BASE_URL))
        self.assertRaises(NoDataHandler, bot.run)

    def test_exception_from_data_handler(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                yield Data('foo', 1)
            
            def data_foo(self, num):
                1/0

        bot = TestSpider()
        bot.setup_queue()
        bot.add_task(Task('page', url=SERVER.BASE_URL))
        bot.run()
        self.assertTrue('data_foo' in bot.items['fatal'][0])
