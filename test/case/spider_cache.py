from unittest import TestCase

from grab.spider import Spider, Task
from test.server import SERVER
from test.util import only_backend

class ContentGenerator():
    def __init__(self):
        self.counter = 0

    def build_html(self):
        self.counter += 1
        return """
        <head>
            <title>ABC</title>
        </head>
        <body>
            <a href="%(BASE_URL)s">link #1</a>
            <a href="%(BASE_URL)s?123">link #2</a>
            <span id="counter">%(COUNTER)s</span>
        </body>
        """ % {'BASE_URL': SERVER.BASE_URL, 'COUNTER': self.counter}

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
            grab.setup(url=SERVER.BASE_URL)
            yield Task('foo', grab=grab, secondary=True, priority=1)

            for count, elem in enumerate(grab.doc.select('//a')):
                yield Task('foo', url=elem.attr('href'), secondary=True,
                           priority=count + 2)


class SpiderCacheMixin(object):
    def setUp(self):
        SERVER.reset()
        SERVER.RESPONSE['get'] = ContentGenerator().build_html

    def test_counter(self):
        bot = SimpleSpider()
        self.setup_cache(bot)
        bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('one', SERVER.BASE_URL))
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

        class Bug1Spider(Spider):
            def task_foo(self, grab, task):
                grab.setup(url=SERVER.BASE_URL)
                yield Task('bar', grab=grab)

            def task_bar(self, grab, task):
                pass

        bot = Bug1Spider()
        self.setup_cache(bot)
        bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('foo', SERVER.BASE_URL))
        bot.run()

    def test_something(self):
        bot = SimpleSpider()
        self.setup_cache(bot)
        bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('foo', SERVER.BASE_URL))
        bot.run()
        self.assertEqual([1, 1, 1, 2], bot.resp_counters)

    def test_timeout(self):
        bot = SimpleSpider()
        self.setup_cache(bot)
        bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('one', SERVER.BASE_URL))
        bot.add_task(Task('one', SERVER.BASE_URL, delay=0.5))
        bot.run()
        self.assertEqual([1, 1], bot.resp_counters)

        bot = SimpleSpider()
        self.setup_cache(bot)
        # DO not clear the cache
        #bot.cache.clear()
        bot.setup_queue()
        bot.add_task(Task('one', SERVER.BASE_URL, priority=1))
        bot.add_task(Task('one', SERVER.BASE_URL, priority=2, cache_timeout=0, delay=1))
        bot.add_task(Task('one', SERVER.BASE_URL, priority=3, cache_timeout=10, delay=1.1))
        bot.add_task(Task('one', SERVER.BASE_URL, priority=4, cache_timeout=0, delay=1.2))
        bot.run()
        self.assertEqual([1, 2, 2, 3], bot.resp_counters)


class SpiderMongoCacheTestCase(SpiderCacheMixin, TestCase):
    _backend = 'mongo'

    def setup_cache(self, bot):
        bot.setup_cache(backend='mongo', database='test_spider')


class SpiderMysqlCacheTestCase(SpiderCacheMixin, TestCase):
    _backend = 'mysql'

    def setup_cache(self, bot):
        bot.setup_cache(backend='mysql', database='spider_test',
                        user='web', passwd='web-**')


class SpiderPostgresqlCacheTestCase(SpiderCacheMixin, TestCase):
    _backend = 'postgresql'

    def setup_cache(self, bot):
        bot.setup_cache(backend='postgresql', database='spider_test')#,
                        #user='web', passwd='web-**')
