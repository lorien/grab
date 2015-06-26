import six
from grab.spider import Spider, Task
from grab.spider.error import SpiderMisuseError
from unittest import TestCase
from grab.spider.queue_backend.base import QueueInterface

from test.util import BaseGrabTestCase, build_spider
from test_settings import MONGODB_CONNECTION, REDIS_CONNECTION


class SpiderQueueMixin(object):
    class SimpleSpider(Spider):
        def task_page(self, grab, task):
            self.stat.collect('url_history', task.url)
            self.stat.collect('priority_history', task.priority)

    def test_basic_priority(self):
        bot = build_spider(self.SimpleSpider, parser_pool_size=1,
                           thread_number=1)
        self.setup_queue(bot)
        bot.task_queue.clear()
        requested_urls = {}
        for priority in (4, 2, 1, 5):
            url = self.server.get_url() + '?p=%d' % priority
            requested_urls[priority] = url
            bot.add_task(Task('page', url=url,
                              priority=priority))
        bot.run()
        urls = [x[1] for x in sorted(requested_urls.items(),
                                     key=lambda x: x[0])]
        self.assertEqual(urls, bot.stat.collections['url_history'])

    def test_queue_length(self):
        bot = build_spider(self.SimpleSpider)
        self.setup_queue(bot)
        bot.task_queue.clear()
        for x in six.moves.range(5):
            bot.add_task(Task('page', url=self.server.get_url()))
        self.assertEqual(5, bot.task_queue.size())
        bot.run()
        self.assertEqual(0, bot.task_queue.size())
        bot.run()

    def test_task_queue_render_stats(self):
        bot = build_spider(self.SimpleSpider)
        bot.render_stats()

    def test_clear(self):
        bot = build_spider(self.SimpleSpider)
        self.setup_queue(bot)
        bot.task_queue.clear()

        for x in six.moves.range(5):
            bot.add_task(Task('page', url=self.server.get_url()))
        self.assertEqual(5, bot.task_queue.size())
        bot.task_queue.clear()
        self.assertEqual(0, bot.task_queue.size())


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
            def task_generator(self):
                yield Task('page', url=server.get_url(), delay=1.5, num=3)
                yield Task('page', url=server.get_url(), delay=4.5, num=2)
                yield Task('page', url=server.get_url(), delay=3, num=4)
                yield Task('page', url=server.get_url(), num=1)

            def task_page(self, grab, task):
                self.stat.collect('numbers', task.num)

        bot = build_spider(TestSpider, thread_number=1)
        self.setup_queue(bot)
        bot.run()
        self.assertEqual(bot.stat.collections['numbers'], [1, 3, 4, 2])

    def test_schedule_list_clear(self):
        bot = build_spider(self.SimpleSpider)
        self.setup_queue(bot)
        bot.task_queue.clear()

        for x in six.moves.range(5):
            bot.add_task(Task('page', url=self.server.get_url(), delay=x+1))

        self.assertEqual(5, len(bot.task_queue.schedule_list))
        bot.task_queue.clear()
        self.assertEqual(0, len(bot.task_queue.schedule_list))


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
            def task_generator(self):
                yield Task('page', url=server.get_url(), num=1)
                yield Task('page', url=server.get_url(), delay=1.5, num=2)
                yield Task('page', url=server.get_url(), delay=0.5, num=3)
                yield Task('page', url=server.get_url(), delay=1, num=4)

            def task_page(self, grab, task):
                self.stat.collect('numbers', task.num)

        bot = build_spider(TestSpider)
        self.setup_queue(bot)
        bot.run()
        self.assertEqual(bot.stat.collections['numbers'], [1, 3, 4, 2])

    def test_clear_collection(self):
        bot = build_spider(self.SimpleSpider)
        self.setup_queue(bot)
        bot.task_queue.clear()


class SpiderRedisQueueTestCase(SpiderQueueMixin, BaseGrabTestCase):
    _backend = 'redis'

    def setup_queue(self, bot):
        bot.setup_queue(backend='redis', **REDIS_CONNECTION)

    def test_delay_error(self):
        bot = build_spider(self.SimpleSpider)
        self.setup_queue(bot)
        bot.task_queue.clear()
        self.assertRaises(SpiderMisuseError,
                          bot.add_task,
                          Task('page', url=self.server.get_url(), delay=1))


class QueueInterfaceTestCase(TestCase):
    def test_abstract_methods(self):
        """Just to improve test coverage"""
        class BrokenQueue(QueueInterface):
            pass

        task_queue = BrokenQueue('spider_name')
        self.assertRaises(NotImplementedError, task_queue.put, None, None)
        self.assertRaises(NotImplementedError, task_queue.get)
        self.assertRaises(NotImplementedError, task_queue.size)
        self.assertRaises(NotImplementedError, task_queue.clear)
