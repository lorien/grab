from unittest import TestCase
import time

from grab.spider import Spider, Task, Data
from util import FakeServerThread, BASE_URL, RESPONSE, SLEEP

class SimpleSpider(Spider):
    def prepare(self):
        self.RESULT = []

    def task_initial(self, grab, task):
        time.sleep(0.2)
        return Data('result', grab.xpath_text('body/h1'))

    def data_result(self, item):
        self.RESULT.append(item)

class TestSpider(TestCase):

           
    def setUp(self):
        FakeServerThread().start()

    def test_spider(self):
        RESPONSE['get'] = '<html><body><h1>light</h1></body></html>'
        sp = SimpleSpider(distributed_mode=True,
                          distributed_path='tests.test_distributed_spider.SimpleSpider')
        for x in xrange(5):
            sp.add_task(Task('initial', url=BASE_URL))
        sp.run()
        self.assertEqual(5, len(sp.RESULT))
        self.assertEqual(set(['light'] * 5), set(sp.RESULT))
