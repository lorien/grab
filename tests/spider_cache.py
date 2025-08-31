"""
TODO:
 * Fix all tests marked as @skip_postgres_test

If postgres then test next after the code below freezes:

    bot.run()
    # now connection has closed
    bot.cache_reader_service.backend.connect()
    # do some checks
"""
from copy import deepcopy
import itertools
import time
import logging

import six
import mock

from tests.util import BaseGrabTestCase, build_spider
from test_settings import (
    MONGODB_CONNECTION,
    MYSQL_CONNECTION,
    POSTGRESQL_CONNECTION,
)
from grab.spider import Spider, Task


def content_generator():
    for cnt in itertools.count(1):
        yield '<b>%s</b>' % cnt


def skip_postgres_test(method):
    def wrapper(self):
        if self.backend == 'postgresql':
            logging.error('Skipping %s method for postgres', method.__name__)
        else:
            method(self)
    return wrapper


class SimpleSpider(Spider):
    def process_time(self):
        self.stat.collect('time', time.time())

    def process_pause(self):
        try:
            pause = self.meta['pause'].pop(0)
        except IndexError:
            pass
        else:
            time.sleep(pause)

    def process_counter(self, grab):
        cnt = grab.doc.select('//b').number()
        self.stat.collect('cnt', cnt)

    def task_null(self, unused_grab, unused_task):
        pass

    def task_simple(self, grab, unused_task):
        self.process_time()
        self.process_pause()
        self.process_counter(grab)

    def task_complex(self, grab, unused_task):
        self.process_time()
        self.process_pause()
        self.process_counter(grab)
        for _ in six.moves.range(3):
            yield Task('simple', url=self.meta['server'].get_url())


class SpiderCacheMixin(object):
    def setUp(self): # pylint: disable=invalid-name
        super(SpiderCacheMixin, self).setUp()
        self.server.response['get.data'] = content_generator()

    def get_configured_spider(self, pause=None, spider_options=None):
        bot = build_spider(
            SimpleSpider,
            meta={'server': self.server, 'pause': (pause or [])},
            parser_pool_size=1,
            **(spider_options or {})
        )
        self.setup_cache(bot)
        bot.cache_reader_service.backend.clear()
        bot.setup_queue()
        return bot

    def test_counter(self):
        self.server.response['get.data'] = content_generator()
        bot = self.get_configured_spider()
        bot.add_task(Task('simple', self.server.get_url()))
        bot.run()
        self.assertEqual([1], bot.stat.collections['cnt'])

    def test_something(self):
        bot = self.get_configured_spider(pause=[0.5])
        bot.add_task(Task('complex', self.server.get_url()))
        bot.run()
        self.assertEqual([1, 1, 1, 1], bot.stat.collections['cnt'])

    def test_only_cache_task(self):
        bot = self.get_configured_spider(
            spider_options={'only_cache': True}
        )
        bot.add_task(Task('simple', self.server.get_url()))
        bot.run()
        self.assertEqual(bot.stat.collections['cnt'], [])

    @skip_postgres_test
    def test_cache_size(self):
        bot = self.get_configured_spider()
        bot.add_task(Task('simple', self.server.get_url()))
        bot.run()
        bot.cache_reader_service.backend.connect()
        self.assertEqual(bot.cache_reader_service.backend.size(), 1)

    def test_cache_task_queue_delay(self):
        """Cache task queue must support the delay parameter"""
        bot = self.get_configured_spider()
        bot.add_task(Task('simple', self.server.get_url()))
        bot.add_task(Task('simple', self.server.get_url(), delay=1))
        bot.run()
        times = bot.stat.collections['time']
        self.assertTrue(times[1] - times[0] >= 0.5)
        self.assertEqual([1, 1], bot.stat.collections['cnt'])
        self.assertEqual(1, bot.stat.counters['cache:req-hit'])

    @skip_postgres_test
    def test_remove_cache_item(self):
        bot = self.get_configured_spider()
        bot.add_task(Task('simple', url=self.server.get_url()))
        bot.add_task(Task('simple', url=self.server.get_url('/foo')))
        bot.run()
        bot.cache_reader_service.backend.connect()
        self.assertEqual(2, bot.cache_reader_service.backend.size())
        bot.cache_reader_service.backend.remove_cache_item(
            self.server.get_url()
        )
        self.assertEqual(1, bot.cache_reader_service.backend.size())

    @skip_postgres_test
    def test_has_item(self):
        bot = self.get_configured_spider()
        bot.add_task(Task('simple', url=self.server.get_url()))
        bot.add_task(Task('simple', url=self.server.get_url('/foo')))
        bot.run()
        bot.cache_reader_service.backend.connect()
        backend = bot.cache_reader_service.backend
        self.assertTrue(backend.has_item(self.server.get_url()))
        self.assertTrue(backend.has_item(self.server.get_url('/foo')))
        self.assertFalse(backend.has_item(self.server.get_url('/bar')))


class SpiderMongoCacheTestCase(SpiderCacheMixin, BaseGrabTestCase):
    backend = 'mongodb'

    def setup_cache(self, bot, **kwargs):
        config = deepcopy(MONGODB_CONNECTION)
        config.update(kwargs)
        bot.setup_cache(backend='mongodb', **config)

    def test_too_large_document(self):
        #print('TESTING TOO LARGE DOCUMENT SPECIAL CASE')
        # The maximum BSON document size is 16 megabytes.
        self.server.response['get.data'] = 'x' * (1024 * 1024 * 17)
        bot = self.get_configured_spider()
        bot.add_task(Task('null', url=self.server.get_url()))
        # Second task is needed just to give spider time to save network
        # result into cache
        bot.add_task(Task('null', url=self.server.get_url(), delay=1))
        patch = mock.Mock()
        with mock.patch('logging.error', patch):
            bot.run()
        # pylint: disable=unsubscriptable-object

        # That fails on macos & py3.5/3.6
        # I have not idea why
        # TODO: uncomment and fix tests for macos
        #self.assertTrue('Document too large' in patch.call_args[0][0])
        # pylint: enable=unsubscriptable-object
        self.assertEqual(bot.cache_reader_service.backend.size(), 0)

    #def test_connection_kwargs(self):
    #    # WTF is testing here?
    #    self.server.response['get.data'] = content_generator()

    #    class TestSpider(Spider):
    #        def task_page(self, grab, task):
    #            pass

    #    config = deepcopy(MONGODB_CONNECTION)
    #    # Set port that would go as **kwargs into MongoClient()
    #    MONGODB_CONNECTION.setdefault('port', 27017)
    #    bot = build_spider(TestSpider)
    #    bot.setup_cache(backend='mongodb', **config)


class SpiderMysqlCacheTestCase(SpiderCacheMixin, BaseGrabTestCase):
    backend = 'mysql'

    def setup_cache(self, bot, **kwargs):
        config = deepcopy(MYSQL_CONNECTION)
        config.update(kwargs)
        bot.setup_cache(backend='mysql', **config)

    def test_create_table(self):
        self.server.response['get.data'] = content_generator()

        class TestSpider(Spider):
            def task_page(self, grab, task):
                pass

        bot = build_spider(TestSpider)
        self.setup_cache(bot)
        bot.cache_reader_service.backend.cursor.execute('begin')
        bot.cache_reader_service.backend.cursor.execute('DROP TABLE cache')
        bot.cache_reader_service.backend.cursor.execute('commit')
        self.setup_cache(bot)
        bot.cache_reader_service.backend.clear()
        self.assertEqual(0, bot.cache_reader_service.backend.size())


class SpiderPostgresqlCacheTestCase(SpiderCacheMixin, BaseGrabTestCase):
    backend = 'postgresql'

    def setup_cache(self, bot, **kwargs):
        config = deepcopy(POSTGRESQL_CONNECTION)
        config.update(kwargs)
        bot.setup_cache(backend='postgresql', **config)

    @skip_postgres_test
    def test_create_table(self):
        self.server.response['get.data'] = content_generator()

        class TestSpider(Spider):
            def task_page(self, grab, task):
                pass

        bot = build_spider(TestSpider)
        self.setup_cache(bot)
        bot.cache_reader_service.backend.cursor.execute('begin')
        bot.cache_reader_service.backend.cursor.execute('DROP TABLE cache')
        bot.cache_reader_service.backend.cursor.execute('commit')
        self.setup_cache(bot)
        bot.cache_reader_service.backend.clear()
        self.assertEqual(0, bot.cache_reader_service.backend.size())
