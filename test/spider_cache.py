# coding: utf-8
from grab.spider import Spider, Task
import mock
from copy import deepcopy

from test.util import BaseGrabTestCase, build_spider
from test_settings import (MONGODB_CONNECTION, MYSQL_CONNECTION,
                           POSTGRESQL_CONNECTION)


class ContentGenerator(object):
    def __init__(self, server):
        self.counter = 0
        self.server = server

    def __iter__(self):
        return self

    def next(self):
        self.counter += 1
        return """
        <head>
            <title>ФЫВА</title>
        </head>
        <body>
            <a href="%(get_url())s">link #1</a>
            <a href="%(get_url())s?123">link #2</a>
            <span id="counter">%(COUNTER)s</span>
        </body>
        """ % {'get_url()': self.server.get_url(), 'COUNTER': self.counter}

    __next__ = next

    def reset(self):
        self.counter = 0


class SimpleSpider(Spider):
    def process_counter(self, grab):
        counter = grab.doc.select('//span[@id="counter"]').number()
        self.stat.collect('resp_counters', counter)

    def task_one(self, grab, task):
        self.process_counter(grab)

    def task_foo(self, grab, task):
        self.process_counter(grab)

        if not task.get('secondary'):
            grab.setup(url=self.meta['server'].get_url())
            yield Task('foo', grab=grab, secondary=True, priority=1)

            for count, elem in enumerate(grab.doc.select('//a')):
                yield Task('foo', url=elem.attr('href'), secondary=True,
                           priority=count + 2)


class SpiderCacheMixin(object):
    def setUp(self):
        self.server.reset()
        self.server.response['get.data'] = ContentGenerator(self.server)

    def test_counter(self):
        bot = build_spider(SimpleSpider, meta={'server': self.server})
        self.setup_cache(bot)
        bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('one', self.server.get_url()))
        bot.run()
        self.assertEqual([1], bot.stat.collections['resp_counters'])

    def test_bug1(self):
        # Test the bug:
        # * enable cache
        # * fetch document (it goes to cache)
        # * request same URL
        # * got exception

        server = self.server

        class Bug1Spider(Spider):
            def task_foo(self, grab, task):
                grab.setup(url=server.get_url())
                yield Task('bar', grab=grab)

            def task_bar(self, grab, task):
                pass

        bot = build_spider(Bug1Spider)
        self.setup_cache(bot)
        bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('foo', self.server.get_url()))
        bot.run()

    def test_something(self):
        bot = build_spider(SimpleSpider, meta={'server': self.server},
                           parser_pool_size=1)
        self.setup_cache(bot)
        bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('foo', self.server.get_url()))
        bot.run()
        self.assertEqual([1, 1, 1, 2], bot.stat.collections['resp_counters'])

    def test_only_cache_task(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                self.stat.collect('points', 1)

        bot = build_spider(TestSpider, only_cache=True)
        self.setup_cache(bot)
        bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('page', self.server.get_url()))
        bot.run()
        self.assertEqual(bot.stat.collections['points'], [])

    def test_cache_size(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                pass

        bot = build_spider(TestSpider)
        self.setup_cache(bot)
        bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('page', self.server.get_url()))
        bot.run()
        self.assertEqual(bot.cache.size(), 1)

    def test_timeout(self):
        bot = build_spider(SimpleSpider, meta={'server': self.server})
        self.setup_cache(bot)
        bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('one', self.server.get_url()))
        bot.add_task(Task('one', self.server.get_url(), delay=2))
        bot.run()
        self.assertEqual(2, bot.stat.counters['spider:request'])
        self.assertEqual(1, bot.stat.counters['spider:request-cache'])
        self.assertEqual([1, 1], bot.stat.collections['resp_counters'])

        bot = build_spider(SimpleSpider, meta={'server': self.server},
                           parser_pool_size=1)
        self.setup_cache(bot)
        # DO not clear the cache
        # bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('one', self.server.get_url(), priority=1))
        bot.add_task(Task('one', self.server.get_url(),
                          priority=2, cache_timeout=0, delay=1))
        bot.add_task(Task('one', self.server.get_url(),
                          priority=3, cache_timeout=10, delay=3))
        bot.add_task(Task('one', self.server.get_url(),
                          priority=4, cache_timeout=0, delay=4))
        bot.run()
        self.assertEqual([1, 2, 2, 3], bot.stat.collections['resp_counters'])

    def test_task_cache_timeout(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                self.stat.collect('points', grab.doc.body)

        bot = build_spider(TestSpider, parser_pool_size=1)
        self.setup_cache(bot)
        bot.cache.clear()
        bot.setup_queue()
        # This task will receive first data from `get.data` iterator
        bot.add_task(Task('page', url=self.server.get_url()))
        # This task will be spawned in 1 second and will
        # receive cached data  (cache timeout = 1.5sec > 1sec)
        bot.add_task(Task('page', url=self.server.get_url(),
                     delay=1, cache_timeout=10))
        # This task will be spawned in 2 seconds and will not
        # receive cached data (cache timeout = 1.5 sec < 2 sec)
        # So, this task will receive next data from `get.data` iterator
        bot.add_task(Task('page', url=self.server.get_url(),
                     delay=2, cache_timeout=0.5))

        self.server.response['get.data'] = iter([b'a', b'b'])
        bot.run()
        self.assertEqual(bot.stat.collections['points'],
                         [b'a', b'a', b'b'])

    def test_remove_cache_item(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                pass

        bot = build_spider(TestSpider)
        self.setup_cache(bot)
        bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.add_task(Task('page', url=self.server.get_url('/foo')))
        bot.run()
        self.assertEqual(2, bot.cache.size())
        bot.cache.remove_cache_item(self.server.get_url())
        self.assertEqual(1, bot.cache.size())

    def test_has_item(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                pass

        bot = build_spider(TestSpider)
        self.setup_cache(bot)
        bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.add_task(Task('page', url=self.server.get_url('/foo')))
        bot.run()
        self.assertTrue(bot.cache.has_item(self.server.get_url()))
        self.assertTrue(bot.cache.has_item(self.server.get_url(), timeout=100))
        self.assertFalse(bot.cache.has_item(self.server.get_url(), timeout=0))
        self.assertTrue(bot.cache.has_item(self.server.get_url('/foo')))
        self.assertFalse(bot.cache.has_item(self.server.get_url('/bar')))


class SpiderMongoCacheTestCase(SpiderCacheMixin, BaseGrabTestCase):
    _backend = 'mongo'

    def setup_cache(self, bot, **kwargs):
        config = deepcopy(MONGODB_CONNECTION)
        config.update(kwargs)
        bot.setup_cache(backend='mongo', **config)

    def test_too_large_document(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                pass

        # The maximum BSON document size is 16 megabytes.
        self.server.response['get.data'] = 'x' * (1024 * 1024 * 17)
        bot = build_spider(TestSpider)
        self.setup_cache(bot, use_compression=False)
        bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        patch = mock.Mock()
        with mock.patch('logging.error', patch):
            bot.run()
        self.assertEqual(bot.cache.size(), 0)
        self.assertTrue('Document too large' in patch.call_args[0][0])

    def test_connection_kwargs(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                pass

        config = deepcopy(MONGODB_CONNECTION)
        # Set port that would go as **kwargs into MongoClient()
        MONGODB_CONNECTION.setdefault('port', 27017)
        bot = build_spider(TestSpider)
        bot.setup_cache(backend='mongo', **config)


class SpiderMysqlCacheTestCase(SpiderCacheMixin, BaseGrabTestCase):
    _backend = 'mysql'

    def setup_cache(self, bot, **kwargs):
        config = deepcopy(MYSQL_CONNECTION)
        config.update(kwargs)
        bot.setup_cache(backend='mysql', **config)

    def test_create_table(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                pass

        bot = build_spider(TestSpider)
        self.setup_cache(bot)
        bot.cache.cursor.execute('begin')
        bot.cache.cursor.execute('DROP TABLE cache')
        bot.cache.cursor.execute('commit')
        self.setup_cache(bot)
        bot.cache.clear()
        self.assertEqual(0, bot.cache.size())


class SpiderPostgresqlCacheTestCase(SpiderCacheMixin, BaseGrabTestCase):
    _backend = 'postgresql'

    def setup_cache(self, bot, **kwargs):
        config = deepcopy(POSTGRESQL_CONNECTION)
        config.update(kwargs)
        bot.setup_cache(backend='postgresql', **config)

    def test_create_table(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                pass

        bot = build_spider(TestSpider)
        self.setup_cache(bot)
        bot.cache.cursor.execute('begin')
        bot.cache.cursor.execute('DROP TABLE cache')
        bot.cache.cursor.execute('commit')
        self.setup_cache(bot)
        bot.cache.clear()
        self.assertEqual(0, bot.cache.size())
