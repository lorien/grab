from unittest import TestCase

from grab.spider import Spider, Task, Data
from .tornado_util import SERVER
from .mixin.spider_queue import SpiderQueueMixin

class BasicSpiderTestCase(TestCase, SpiderQueueMixin):
    def setUp(self):
        SERVER.reset()

    def setup_queue(self, bot):
        bot.setup_queue(backend='memory')

    def test_schedule(self):
        """
        In this test I create a number of delayed task
        and then check the order in which they was executed
        """

        class TestSpider(Spider):
            def prepare(self):
                self.numbers = []

            def task_generator(self):
                yield Task('page', url=SERVER.BASE_URL, num=1)
                yield Task('page', url=SERVER.BASE_URL, delay=1.5, num=2)
                yield Task('page', url=SERVER.BASE_URL, delay=0.5, num=3)
                yield Task('page', url=SERVER.BASE_URL, delay=1, num=4)

            def task_page(self, grab, task):
                self.numbers.append(task.num)

        bot = TestSpider()
        self.setup_queue(bot)
        bot.run()
        self.assertEqual(bot.numbers, [1, 3, 4, 2])
