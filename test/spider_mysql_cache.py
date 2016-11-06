from unittest import TestCase

from .mixin.spider_cache import SpiderCacheMixin
from test_settings import MYSQL_CONNECTION


class BasicSpiderTestCase(TestCase, SpiderCacheMixin):
    def setUp(self):
        SpiderCacheMixin.setUp(self)

    def setup_cache(self, bot):
        bot.setup_cache(backend='mysql', **MYSQL_CONNECTION)
