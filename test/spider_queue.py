import six
from grab.spider import Spider, Task
from grab.spider.error import SpiderMisuseError
from unittest import TestCase
from grab.spider.queue_backend.base import QueueInterface

from test.util import BaseGrabTestCase
from test_settings import MONGODB_CONNECTION, REDIS_CONNECTION


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
            url = self.server.get_url() + '?p=%d' % priority
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
        for x in six.moves.range(5):
            bot.add_task(Task('page', url=self.server.get_url()))
        self.assertEqual(5, bot.taskq.size())
        bot.run()
        self.assertEqual(0, bot.taskq.size())
        bot.run()

    def test_taskq_render_stats(self):
        bot = self.SimpleSpider()
        bot.render_stats()


class SpiderMemoryQueueTestCase(BaseGrabTestCase, SpiderQueueMixin):
    def setup_queue(self, bot):
        bot.setup_queue(backend='memory')

    def test_schedule(self):
        """
        In this test I create a number of delayed task
        and then check the order in which they was executed
        """
        server = self.server

        class TestSpider(Spider):
            def prepare(self):
                self.numbers = []

            def task_generator(self):
                yield Task('page', url=server.get_url(), num=1)
                yield Task('page', url=server.get_url(), delay=1.5, num=2)
                yield Task('page', url=server.get_url(), delay=0.5, num=3)
                yield Task('page', url=server.get_url(), delay=1, num=4)

            def task_page(self, grab, task):
                self.numbers.append(task.num)

        bot = TestSpider()
        self.setup_queue(bot)
        bot.run()
        self.assertEqual(bot.numbers, [1, 3, 4, 2])


class BasicSpiderTestCase(SpiderQueueMixin, BaseGrabTestCase):
    _backend = 'mongo'

    def setup_queue(self, bot):
        bot.setup_queue(backend='mongo', **MONGODB_CONNECTION)

    def test_schedule(self):
        """
        In this test I create a number of delayed task
        and then check the order in which they was executed
        """
        server = self.server

        class TestSpider(Spider):
            def prepare(self):
                self.numbers = []

            def task_generator(self):
                yield Task('page', url=server.get_url(), num=1)
                yield Task('page', url=server.get_url(), delay=1.5, num=2)
                yield Task('page', url=server.get_url(), delay=0.5, num=3)
                yield Task('page', url=server.get_url(), delay=1, num=4)

            def task_page(self, grab, task):
                self.numbers.append(task.num)

        bot = TestSpider()
        self.setup_queue(bot)
        bot.run()
        self.assertEqual(bot.numbers, [1, 3, 4, 2])

    def test_clear_collection(self):
        bot = self.SimpleSpider()
        self.setup_queue(bot)
        bot.taskq.clear()


class SpiderRedisQueueTestCase(SpiderQueueMixin, BaseGrabTestCase):
    _backend = 'redis'

    def setup_queue(self, bot):
        bot.setup_queue(backend='redis', **REDIS_CONNECTION)

    def test_delay_error(self):
        bot = self.SimpleSpider()
        self.setup_queue(bot)
        bot.taskq.clear()
        self.assertRaises(SpiderMisuseError,
                          bot.add_task,
                          Task('page', url=self.server.get_url(), delay=1))


class QueueInterfaceTestCase(TestCase):
    def test_abstract_methods(self):
        """Just to improve test coverage"""
        class BrokenQueue(QueueInterface):
            pass

        taskq = BrokenQueue('spider_name')
        self.assertRaises(NotImplementedError, taskq.put, None, None)
        self.assertRaises(NotImplementedError, taskq.get)
        self.assertRaises(NotImplementedError, taskq.size)
        self.assertRaises(NotImplementedError, taskq.clear)
