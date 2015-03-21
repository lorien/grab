from grab.spider import Spider, Task

from test.util import BaseGrabTestCase
from test_settings import MONGODB_CONNECTION, MYSQL_CONNECTION


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
            <title>ABC</title>
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
    def prepare(self):
        self.resp_counters = []

    def process_counter(self, grab):
        counter = grab.doc.select('//span[@id="counter"]').number()
        self.resp_counters.append(counter)

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
        bot = SimpleSpider(meta={'server': self.server})
        self.setup_cache(bot)
        bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('one', self.server.get_url()))
        bot.run()
        self.assertEqual([1], bot.resp_counters)

    def test_bug1(self):
        """
        Test the bug:
        * enable cache
        * fetch document (it goes to cache)
        * request same URL
        * got exception
        """

        server = self.server

        class Bug1Spider(Spider):
            def task_foo(self, grab, task):
                grab.setup(url=server.get_url())
                yield Task('bar', grab=grab)

            def task_bar(self, grab, task):
                pass

        bot = Bug1Spider()
        self.setup_cache(bot)
        bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('foo', self.server.get_url()))
        bot.run()

    def test_something(self):
        bot = SimpleSpider(meta={'server': self.server})
        self.setup_cache(bot)
        bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('foo', self.server.get_url()))
        bot.run()
        self.assertEqual([1, 1, 1, 2], bot.resp_counters)

    def test_timeout(self):
        bot = SimpleSpider(meta={'server': self.server})
        self.setup_cache(bot)
        bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('one', self.server.get_url()))
        bot.add_task(Task('one', self.server.get_url(), delay=0.5))
        bot.run()
        self.assertEqual([1, 1], bot.resp_counters)

        bot = SimpleSpider(meta={'server': self.server})
        self.setup_cache(bot)
        # DO not clear the cache
        # bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('one', self.server.get_url(), priority=1))
        bot.add_task(Task('one', self.server.get_url(),
                          priority=2, cache_timeout=0, delay=1))
        bot.add_task(Task('one', self.server.get_url(),
                          priority=3, cache_timeout=10, delay=1.1))
        bot.add_task(Task('one', self.server.get_url(),
                          priority=4, cache_timeout=0, delay=1.2))
        bot.run()
        self.assertEqual([1, 2, 2, 3], bot.resp_counters)


class SpiderMongoCacheTestCase(SpiderCacheMixin, BaseGrabTestCase):
    _backend = 'mongo'

    def setup_cache(self, bot):
        bot.setup_cache(backend='mongo', **MONGODB_CONNECTION)


class SpiderMysqlCacheTestCase(SpiderCacheMixin, BaseGrabTestCase):
    _backend = 'mysql'

    def setup_cache(self, bot):
        bot.setup_cache(backend='mysql', **MYSQL_CONNECTION)


class SpiderPostgresqlCacheTestCase(SpiderCacheMixin, BaseGrabTestCase):
    _backend = 'postgresql'

    def setup_cache(self, bot):
        bot.setup_cache(backend='postgresql', database='spider_test')
