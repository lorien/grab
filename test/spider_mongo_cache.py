from unittest import TestCase

from test.mixin.spider_cache import SpiderCacheMixin


class BasicSpiderTestCase(TestCase, SpiderCacheMixin):
    def setUp(self):
        SpiderCacheMixin.setUp(self)

    def setup_cache(self, bot):
        bot.setup_cache(backend='mongo', database='test_spider')
