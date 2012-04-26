# coding: utf-8

from random import shuffle
from unittest import TestCase, main

from grab.spider import Spider, Task

from util import FakeServerThread, RESPONSE, SLEEP, BASE_URL


class TestSpider(TestCase):
    TASKS_COUNT = 10

    def setUp(self):
        FakeServerThread().start()

    def test_spider(self):
        class FirstSpider(Spider):
            initial_urls = ['%s/%s' % (BASE_URL, 'first')]

        class SecondSpider(Spider):
            initial_urls = ['%s/%s' % (BASE_URL, 'second')]

        class SimpleSpider(FirstSpider, SecondSpider):
            def prepare(self):
                self.looked_urls = set()

            def task_initial(self, grab, task):
                self.looked_urls.append(grab.response.url)

        RESPONSE['get'] = 'Hello spider!'
        SLEEP['get'] = 0

        sp = SimpleSpider(thread_number=TestSpider.TASKS_COUNT * 2)
        sp.run()

        good_looked_urls = set(FirstSpider.initial_urls + SecondSpider.initial_urls)

        self.assertSetEqual(good_looked_urls, sp.looked_urls)


if __name__ == '__main__':
    main()
