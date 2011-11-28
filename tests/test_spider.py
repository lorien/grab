from unittest import TestCase

from grab.spider import Spider, Task, Data
from util import FakeServerThread, BASE_URL, RESPONSE, SLEEP

class TestSpider(TestCase):

    class SimpleSpider(Spider):
        def task_baz(self, grab, task):
            return Data('foo', grab.response.body)

        def data_foo(self, item):
            self.SAVED_ITEM = item
           
    def setUp(self):
        FakeServerThread().start()

    def test_spider(self):
        RESPONSE['get'] = 'Hello spider!'
        SLEEP['get'] = 0
        sp = self.SimpleSpider()
        sp.add_task(Task('baz', BASE_URL))
        sp.run()
        self.assertEqual('Hello spider!', sp.SAVED_ITEM)

    def test_network_limit(self):
        RESPONSE['get'] = 'Hello spider!'
        SLEEP['get'] = 1.1

        sp = self.SimpleSpider(network_try_limit=1)
        sp.setup_grab(connect_timeout=1, timeout=1)
        sp.add_task(Task('baz', BASE_URL))
        sp.run()
        self.assertEqual(sp.counters['request-network'], 1)

        sp = self.SimpleSpider(network_try_limit=2)
        sp.setup_grab(connect_timeout=1, timeout=1)
        sp.add_task(Task('baz', BASE_URL))
        sp.run()
        self.assertEqual(sp.counters['request-network'], 2)

    def test_task_limit(self):
        RESPONSE['get'] = 'Hello spider!'
        SLEEP['get'] = 1.1

        sp = self.SimpleSpider(network_try_limit=1)
        sp.setup_grab(connect_timeout=1, timeout=1)
        sp.add_task(Task('baz', BASE_URL))
        sp.run()
        self.assertEqual(sp.counters['task-baz'], 1)

        sp = self.SimpleSpider(task_try_limit=2)
        sp.add_task(Task('baz', BASE_URL, task_try_count=3))
        sp.run()
        self.assertEqual(sp.counters['request-network'], 0)
