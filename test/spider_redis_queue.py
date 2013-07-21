from unittest import TestCase

from grab.spider import Spider, Task, Data
from .tornado_util import SERVER
from .mixin.spider_queue import SpiderQueueMixin

class SpiderRedisQueueTestCase(TestCase, SpiderQueueMixin):
    def setUp(self):
        SERVER.reset()

    def setup_queue(self, bot):
        bot.setup_queue(backend='redis')
