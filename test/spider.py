import six
from grab.spider import Spider, Task
from grab.spider.error import SpiderError, FatalError
import os
import signal
import mock

from test.util import BaseGrabTestCase, build_spider


class BasicSpiderTestCase(BaseGrabTestCase):
    class SimpleSpider(Spider):
        def task_baz(self, grab, task):
            self.stat.collect('SAVED_ITEM', grab.response.body)

    def setUp(self):
        self.server.reset()

    def test_spider(self):
        self.server.response['get.data'] = 'Hello spider!'
        self.server.response['sleep'] = 0
        bot = build_spider(self.SimpleSpider)
        bot.setup_queue()
        bot.add_task(Task('baz', self.server.get_url()))
        bot.run()
        self.assertEqual(b'Hello spider!',
                         bot.stat.collections['SAVED_ITEM'][0])

    def test_network_limit(self):
        self.server.response['get.data'] = 'Hello spider!'
        self.server.response['sleep'] = 1.1

        bot = build_spider(self.SimpleSpider, network_try_limit=1)
        bot.setup_queue()
        bot.setup_grab(connect_timeout=1, timeout=1)
        bot.add_task(Task('baz', self.server.get_url()))
        bot.run()
        self.assertEqual(bot.stat.counters['spider:request-network'], 1)

        bot = build_spider(self.SimpleSpider, network_try_limit=2)
        bot.setup_queue()
        bot.setup_grab(connect_timeout=1, timeout=1)
        bot.add_task(Task('baz', self.server.get_url()))
        bot.run()
        self.assertEqual(bot.stat.counters['spider:request-network'], 2)

    def test_task_limit(self):
        self.server.response['get.data'] = 'Hello spider!'
        self.server.response['sleep'] = 1.1

        bot = build_spider(self.SimpleSpider, network_try_limit=1)
        bot.setup_grab(connect_timeout=1, timeout=1)
        bot.setup_queue()
        bot.add_task(Task('baz', self.server.get_url()))
        bot.run()
        self.assertEqual(bot.stat.counters['spider:task-baz'], 1)

        bot = build_spider(self.SimpleSpider, task_try_limit=2)
        bot.setup_queue()
        bot.add_task(Task('baz', self.server.get_url(), task_try_count=3))
        bot.run()
        self.assertEqual(bot.stat.counters['spider:request-network'], 0)

    def test_task_retry(self):
        self.server.response['get.data'] = 'xxx'
        self.server.response_once['code'] = 403
        bot = build_spider(self.SimpleSpider)
        bot.setup_queue()
        bot.add_task(Task('baz', self.server.get_url()))
        bot.run()
        self.assertEqual(b'xxx', bot.stat.collections['SAVED_ITEM'][0])

    def test_setup_grab(self):
        # Mulitple calls to `setup_grab` should accumulate
        # changes in config object.
        bot = build_spider(self.SimpleSpider)
        bot.setup_grab(log_dir='/tmp')
        bot.setup_grab(timeout=30)
        grab = bot.create_grab_instance()
        self.assertEqual(grab.config['log_dir'], '/tmp')
        self.assertEqual(grab.config['timeout'], 30)

    def test_generator(self):
        server = self.server

        class TestSpider(Spider):
            def task_generator(self):
                for x in six.moves.range(1111):
                    yield Task('page', url=server.get_url())

            def task_page(self, grab, task):
                self.stat.inc('count')

        bot = build_spider(TestSpider)
        bot.run()
        self.assertEqual(bot.stat.counters['count'], 1111)

    def test_get_spider_name(self):
        class TestSpider(Spider):
            pass

        self.assertEqual('test_spider', TestSpider.get_spider_name())

        class TestSpider(Spider):
            spider_name = 'foo_bar'

        self.assertEqual('foo_bar', TestSpider.get_spider_name())

    def test_handler_result_none(self):
        class TestSpider(Spider):
            def prepare(self):
                self.points = []

            def task_page(self, grab, task):
                yield None

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.run()

    """
    # DOES NOT WORK
    def test_keyboard_interrupt(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                os.kill(os.getpid(), signal.SIGINT)

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.run()
        self.assertTrue(bot.interrupted)
    """

    def test_fallback_handler_by_default_name(self):
        class TestSpider(Spider):
            def prepare(self):
                self.points = []

            def task_page(self, grab, task):
                pass

            def task_page_fallback(self, task):
                self.points.append(1)

        self.server.response['code'] = 403

        bot = build_spider(TestSpider, network_try_limit=1)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.run()
        self.assertEquals(bot.points, [1])

    def test_fallback_handler_by_fallback_name(self):
        class TestSpider(Spider):
            def prepare(self):
                self.points = []

            def task_page(self, grab, task):
                pass

            def fallback_zz(self, task):
                self.points.append(1)

        self.server.response['code'] = 403

        bot = build_spider(TestSpider, network_try_limit=1)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url(),
                          fallback_name='fallback_zz'))
        bot.run()
        self.assertEquals(bot.points, [1])

    #AFTER THIS: BAD
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
                self.points = []

            def task_page(self, grab, task):
                yield 1

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        #bot.run()
        #self.assertEqual(1, bot.stat.counters['spider:error-spidererror'])
        self.assertRaises(SpiderError, bot.run)

    def test_fatal_error(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                raise FatalError

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        self.assertRaises(FatalError, bot.run)

    def test_task_queue_clear(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                self.stop()

            def task_keyboard_interrupt_page(self, grab, task):
                raise KeyboardInterrupt

        bot = build_spider(TestSpider)
        bot.setup_queue()
        for x in six.moves.range(5):
            bot.add_task(Task('page', url=self.server.get_url()))
        self.assertEqual(5, bot.task_queue.size())
        bot.run()
        self.assertEqual(0, bot.task_queue.size())

        for x in six.moves.range(5):
            bot.add_task(Task('keyboard_interrupt_page', url=self.server.get_url()))
        self.assertEqual(5, bot.task_queue.size())
        bot.run()
        self.assertEqual(0, bot.task_queue.size())
