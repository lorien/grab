import six
from grab import Grab
from grab.spider import Spider, Task
from grab.spider.error import SpiderError, FatalError

from tests.util import BaseGrabTestCase, build_spider


class SimpleSpider(Spider):
    def task_baz(self, grab, unused_task):
        self.stat.collect('SAVED_ITEM', grab.doc.body)


class BasicSpiderTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_spider(self):
        self.server.response['get.data'] = 'Hello spider!'
        self.server.response['sleep'] = 0
        bot = build_spider(SimpleSpider)
        bot.setup_queue()
        bot.add_task(Task('baz', self.server.get_url()))
        bot.run()
        self.assertEqual(b'Hello spider!',
                         bot.stat.collections['SAVED_ITEM'][0])

    def test_network_limit(self):
        class CustomSimpleSpider(SimpleSpider):
            def create_grab_instance(self, **kwargs):
                return Grab(connect_timeout=1, timeout=1)

        self.server.response['get.data'] = 'Hello spider!'
        self.server.response['sleep'] = 1.1

        bot = build_spider(CustomSimpleSpider, network_try_limit=1)
        bot.setup_queue()
        #bot.setup_grab(connect_timeout=1, timeout=1)
        bot.add_task(Task('baz', self.server.get_url()))
        bot.run()
        self.assertEqual(bot.stat.counters['spider:request-network'], 1)

        bot = build_spider(CustomSimpleSpider, network_try_limit=2)
        bot.setup_queue()
        #bot.setup_grab(connect_timeout=1, timeout=1)
        bot.add_task(Task('baz', self.server.get_url()))
        bot.run()
        self.assertEqual(bot.stat.counters['spider:request-network'], 2)

    def test_task_limit(self):
        class CustomSimpleSpider(SimpleSpider):
            def create_grab_instance(self, **kwargs):
                return Grab(connect_timeout=1, timeout=1)

        self.server.response['get.data'] = 'Hello spider!'
        self.server.response['sleep'] = 1.1

        bot = build_spider(CustomSimpleSpider, network_try_limit=1)
        #bot.setup_grab(connect_timeout=1, timeout=1)
        bot.setup_queue()
        bot.add_task(Task('baz', self.server.get_url()))
        bot.run()
        self.assertEqual(bot.stat.counters['spider:task-baz'], 1)

        bot = build_spider(SimpleSpider, task_try_limit=2)
        bot.setup_queue()
        bot.add_task(Task('baz', self.server.get_url(), task_try_count=3))
        bot.run()
        self.assertEqual(bot.stat.counters['spider:request-network'], 0)

    def test_task_retry(self):
        self.server.response['get.data'] = 'xxx'
        self.server.response_once['code'] = 403
        bot = build_spider(SimpleSpider)
        bot.setup_queue()
        bot.add_task(Task('baz', self.server.get_url()))
        bot.run()
        self.assertEqual(b'xxx', bot.stat.collections['SAVED_ITEM'][0])

    def test_generator(self):
        server = self.server

        class TestSpider(Spider):
            def task_generator(self):
                for _ in six.moves.range(1111):
                    yield Task('page', url=server.get_url())

            def task_page(self, unused_grab, unused_task):
                self.stat.inc('count')

        bot = build_spider(TestSpider)
        bot.run()
        self.assertEqual(bot.stat.counters['count'], 1111)

    def test_get_spider_name(self):
        class TestSpider(Spider):
            pass

        self.assertEqual('test_spider', TestSpider.get_spider_name())

        class TestSpider2(Spider):
            spider_name = 'foo_bar'

        self.assertEqual('foo_bar', TestSpider2.get_spider_name())

    def test_handler_result_none(self):
        class TestSpider(Spider):
            def prepare(self):
                # pylint: disable=attribute-defined-outside-init
                self.points = []

            def task_page(self, unused_grab, unused_task):
                yield None

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.run()

    def test_fallback_handler_by_default_name(self):
        class TestSpider(Spider):
            def prepare(self):
                # pylint: disable=attribute-defined-outside-init
                self.points = []

            def task_page(self, grab, task):
                pass

            def task_page_fallback(self, unused_task):
                self.points.append(1)

        self.server.response['code'] = 403

        bot = build_spider(TestSpider, network_try_limit=1)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.run()
        self.assertEqual(bot.points, [1])

    def test_fallback_handler_by_fallback_name(self):
        class TestSpider(Spider):
            def prepare(self):
                # pylint: disable=attribute-defined-outside-init
                self.points = []

            def task_page(self, grab, task):
                pass

            def fallback_zz(self, unused_task):
                self.points.append(1)

        self.server.response['code'] = 403

        bot = build_spider(TestSpider, network_try_limit=1)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url(),
                          fallback_name='fallback_zz'))
        bot.run()
        self.assertEqual(bot.points, [1])

    def test_check_task_limits_invalid_value(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                pass

            def check_task_limits(self, task):
                return False, 'zz'

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url(),
                          fallback_name='fallback_zz'))
        self.assertRaises(SpiderError, bot.run)

    def test_handler_result_invalid(self):
        class TestSpider(Spider):
            def prepare(self):
                # pylint: disable=attribute-defined-outside-init
                self.points = []

            def task_page(self, unused_grab, unused_task):
                yield 1

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        #bot.run()
        #self.assertEqual(1, bot.stat.counters['spider:error-spidererror'])
        self.assertRaises(SpiderError, bot.run)

    def test_task_queue_clear(self):
        class TestSpider(Spider):
            def task_page(self, unused_grab, unused_task):
                self.stop()

        bot = build_spider(TestSpider)
        bot.setup_queue()
        for _ in six.moves.range(5):
            bot.add_task(Task('page', url=self.server.get_url()))
        self.assertEqual(5, bot.task_queue.size())
        bot.run()
        self.assertEqual(0, bot.task_queue.size())

    def test_fatal_error(self):
        class TestSpider(Spider):
            def task_page(self, unused_grab, unused_task):
                raise FatalError

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        self.assertRaises(FatalError, bot.run)
