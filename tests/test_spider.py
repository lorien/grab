from unittest import TestCase

from grab.spider import Spider, Task, Data
from util import FakeServerThread, BASE_URL, RESPONSE

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
        sp = self.SimpleSpider()
        sp.add_task(Task('baz', BASE_URL))
        sp.run()
        self.assertEqual('Hello spider!', sp.SAVED_ITEM)
