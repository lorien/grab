import six
from grab.spider import Spider, Task, NullTask
from grab.spider.error import SpiderError, FatalError
import os
import signal
import mock

from test.util import BaseGrabTestCase


class BasicSpiderTestCase(BaseGrabTestCase):

    class SimpleSpider(Spider):
        def task_baz(self, grab, task):
            self.SAVED_ITEM = grab.response.body

    def setUp(self):
        self.server.reset()

    def test_spider(self):
        self.server.response['get.data'] = 'Hello spider!'
        self.server.response['sleep'] = 0
        sp = self.SimpleSpider()
        sp.setup_queue()
        sp.add_task(Task('baz', self.server.get_url()))
        sp.run()
        self.assertEqual(b'Hello spider!', sp.SAVED_ITEM)

    def test_network_limit(self):
        self.server.response['get.data'] = 'Hello spider!'
        self.server.response['sleep'] = 1.1

        sp = self.SimpleSpider(network_try_limit=1)
        sp.setup_queue()
        sp.setup_grab(connect_timeout=1, timeout=1)
        sp.add_task(Task('baz', self.server.get_url()))
        sp.run()
        self.assertEqual(sp.counters['request-network'], 1)

        sp = self.SimpleSpider(network_try_limit=2)
        sp.setup_queue()
        sp.setup_grab(connect_timeout=1, timeout=1)
        sp.add_task(Task('baz', self.server.get_url()))
        sp.run()
        self.assertEqual(sp.counters['request-network'], 2)

    def test_task_limit(self):
        self.server.response['get.data'] = 'Hello spider!'
        self.server.response['sleep'] = 1.1

        sp = self.SimpleSpider(network_try_limit=1)
        sp.setup_grab(connect_timeout=1, timeout=1)
        sp.setup_queue()
        sp.add_task(Task('baz', self.server.get_url()))
        sp.run()
        self.assertEqual(sp.counters['task-baz'], 1)

        sp = self.SimpleSpider(task_try_limit=2)
        sp.setup_queue()
        sp.add_task(Task('baz', self.server.get_url(), task_try_count=3))
        sp.run()
        self.assertEqual(sp.counters['request-network'], 0)

    def test_task_retry(self):
        self.server.response['get.data'] = 'xxx'
        self.server.response_once['code'] = 403
        sp = self.SimpleSpider()
        sp.setup_queue()
        sp.add_task(Task('baz', self.server.get_url()))
        sp.run()
        self.assertEqual(b'xxx', sp.SAVED_ITEM)

    def test_setup_grab(self):
        # Mulitple calls to `setup_grab` should accumulate
        # changes in config object.
        bot = self.SimpleSpider()
        bot.setup_grab(log_dir='/tmp')
        bot.setup_grab(timeout=30)
        grab = bot.create_grab_instance()
        self.assertEqual(grab.config['log_dir'], '/tmp')
        self.assertEqual(grab.config['timeout'], 30)

    def test_generator(self):
        server = self.server

        class TestSpider(Spider):
            def prepare(self):
                self.count = 0

            def task_generator(self):
                for x in six.moves.range(1111):
                    yield Task('page', url=server.get_url())

            def task_page(self, grab, task):
                self.count += 1

        bot = TestSpider()
        bot.run()
        self.assertEqual(bot.count, 1111)

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

        bot = TestSpider()
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.run()

    def test_handler_result_invalid(self):
        class TestSpider(Spider):
            def prepare(self):
                self.points = []

            def task_page(self, grab, task):
                yield 1

        bot = TestSpider()
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        bot.run()
        self.assertEqual(1, bot.counters['error-spidererror'])

    """
    # DOES NOT WORK
    def test_keyboard_interrupt(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                os.kill(os.getpid(), signal.SIGINT)

        bot = TestSpider()
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

        bot = TestSpider(network_try_limit=1)
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

        bot = TestSpider(network_try_limit=1)
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url(),
                          fallback_name='fallback_zz'))
        bot.run()
        self.assertEquals(bot.points, [1])

    def test_check_task_limits_invalid_value(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                pass

            def check_task_limits(self, task):
                return False, 'zz'

        bot = TestSpider()
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url(),
                          fallback_name='fallback_zz'))
        self.assertRaises(SpiderError, bot.run)

    def test_null_task(self):
        class TestSpider(Spider):
            pass


        bot = TestSpider()
        bot.setup_queue()
        bot.add_task(NullTask(sleep=0.3))

        points = []
        def sleep(arg):
            points.append(arg)


        with mock.patch('time.sleep', sleep):
            bot.run()

        self.assertEqual(points, [0.3])

    def test_fatal_error(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                raise FatalError

        bot = TestSpider()
        bot.setup_queue()
        bot.add_task(Task('page', url=self.server.get_url()))
        self.assertRaises(FatalError, bot.run)
