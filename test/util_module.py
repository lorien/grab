from unittest import TestCase
from grab.util.module import (build_spider_registry, SPIDER_REGISTRY,
                              load_spider_class)
from grab.spider import Spider
from grab.spider.error import SpiderInternalError
from test.util import TMP_DIR
import os
import sys

class BaseSpider(Spider):
    class Meta:
        abstract = True


class FirstSpider(BaseSpider):
    pass


class SecondSpider(BaseSpider):
    pass


class UtilModuleTestCase(TestCase):
    def build_config(self, modules):
        cfg = {'global': {'spider_modules': modules}}
        return cfg

    def test_build_spider_registry(self):
        cfg = self.build_config(['test.util_module', 'zz'])
        reg = build_spider_registry(cfg)
        self.assertEqual(reg, SPIDER_REGISTRY)

    def test_build_spider_registry_with_name(self):
        cfg = self.build_config(['test.util_module', 'zz'])
        reg = build_spider_registry(cfg)
        self.assertEqual(2, len(reg))

        cfg = self.build_config(['test.util_module:SecondSpider', 'zz'])
        reg = build_spider_registry(cfg)
        self.assertEqual(1, len(reg))

    def test_build_spider_registry_failed_module(self):
        cfg = self.build_config(['test.util_module', 'zz',
                                 'test.files.invalid_import'])
        reg = build_spider_registry(cfg)
        self.assertEqual(2, len(reg))

    def test_build_spider_registry_same_name_spiders(self):
        cfg = self.build_config(['test.util_module', 'zz',
                                 'test.files.first_spider'])
        self.assertRaises(SpiderInternalError, build_spider_registry, cfg)

    def test_load_spider_class(self):
        cfg = self.build_config(['test.util_module'])
        SPIDER_REGISTRY.clear()
        cls = load_spider_class(cfg, 'first_spider')
        self.assertEqual(cls, FirstSpider)

    def test_load_spider_class_error(self):
        cfg = self.build_config(['test.util_module'])
        reg = build_spider_registry(cfg)
        self.assertRaises(SpiderInternalError, load_spider_class,
                          cfg, 'first_spider_zzz')
