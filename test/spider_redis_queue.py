from unittest import TestCase

from grab.spider import Spider, Task, Data
from util import FakeServerThread, BASE_URL, RESPONSE, SLEEP
from mixin.spider_queue import SpiderQueueMixin

class BasicSpiderTestCase(TestCase, SpiderQueueMixin):
    def setUp(self):
        FakeServerThread().start()

    def setup_queue(self, bot):
        bot.setup_queue(backend='redis')
