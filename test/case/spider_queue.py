from unittest import TestCase

from grab.spider import Spider, Task, Data
from test.server import SERVER

from grab.util.py3k_support import *

class SpiderQueueMixin(object):
    class SimpleSpider(Spider):
        def prepare(self):
            self.url_history = []
            self.priority_history = []

        def task_page(self, grab, task):
            self.url_history.append(task.url)
            self.priority_history.append(task.priority)

    def test_basic_priority(self):
        bot = self.SimpleSpider()
        self.setup_queue(bot)
        bot.taskq.clear()
        requested_urls = {}
        for priority in (4, 2, 1, 5):
            url = SERVER.BASE_URL + '?p=%d' % priority
            requested_urls[priority] = url
            bot.add_task(Task('page', url=url,
                              priority=priority))
        bot.run()
        urls = [x[1] for x in sorted(requested_urls.items(), 
                                     key=lambda x: x[0])]
        self.assertEqual(urls, bot.url_history)

    def test_queue_length(self):
        bot = self.SimpleSpider()
        self.setup_queue(bot)
        bot.taskq.clear()
        for x in xrange(5):
            bot.add_task(Task('page', url=SERVER.BASE_URL))
        self.assertEqual(5, bot.taskq.size())
        bot.run()
        self.assertEqual(0, bot.taskq.size())
        bot.run()


class SpiderMemoryQueueTestCase(TestCase, SpiderQueueMixin):
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


class BasicSpiderTestCase(SpiderQueueMixin, TestCase):
    _backend = 'mongo'

    def setup_queue(self, bot):
        bot.setup_queue(backend='mongo', database='queue_test')


class SpiderRedisQueueTestCase(SpiderQueueMixin, TestCase):
    _backend = 'redis'

    def setup_queue(self, bot):
        bot.setup_queue(backend='redis')
