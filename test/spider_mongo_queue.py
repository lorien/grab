# coding: utf-8

from random import shuffle
from unittest import TestCase, main

from grab.spider import Spider, Task

from util import FakeServerThread, RESPONSE, SLEEP, BASE_URL

class TestSpider(TestCase):
    TASKS_COUNT = 10

    class SimpleSpider(Spider):
        def prepare(self):
            self.tasks = [index for index in xrange(TestSpider.TASKS_COUNT)]
            shuffle(self.tasks)
            self.tasks_order = []

        def setup_queue(self, backend='mongo', database='queue_test', **kwargs):
            super(TestSpider.SimpleSpider, self).setup_queue(backend, database, **kwargs)

        def task_generator(self):
            for index in self.tasks:
                yield Task(
                    name='foo',
                    url=BASE_URL,
                    priority=index,
                    index=index,
                )

        def task_foo(self, grab, task):
            self.tasks_order.append(task.index)

    def setUp(self):
        FakeServerThread().start()

    def test_spider(self):
        RESPONSE['get'] = 'Hello spider!'
        SLEEP['get'] = 0

        sp = TestSpider.SimpleSpider(thread_number=TestSpider.TASKS_COUNT * 2)
        sp.run()

        self.assertEqual(range(TestSpider.TASKS_COUNT), sp.tasks_order)

if __name__ == '__main__':
    main()
