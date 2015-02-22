import six

from grab.spider import Spider, Task
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
        """
        Mulitple calls to `setup_grab` should accumulate
        changes in config object.
        """
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
