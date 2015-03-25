from unittest import TestCase
from grab.util.config import (update_dict, build_root_config,
                              build_spider_config)
from grab.util.default_config import DEFAULT_SPIDER_GLOBAL_CONFIG
from grab.spider import Spider

class UtilConfigTestCase(TestCase):
    def test_update_dict(self):
        self.assertEqual(
            update_dict({}, {'foo': 'new'}),
            {'foo': 'new'})
        self.assertEqual(
            update_dict({'foo': 'new'}, {}),
            {'foo': 'new'})
        self.assertEqual(
            update_dict({'foo': 'old', '1': '2'}, {'foo': 'new'}),
            {'foo': 'old', '1': '2'})
        self.assertEqual(
            update_dict({'foo': 'old', '1': '2'}, {'foo': 'new'},
                        overwrite=True),
            {'foo': 'new', '1': '2'})

    def test_build_root_config_empty_settings(self):
        self.assertRaises(AttributeError, build_root_config,
                          'test.files.settings_empty')

    def test_build_root_config_file_does_not_exist(self):
        self.assertRaises(ImportError, build_root_config,
                          'test.files.settings_zzzzzz')

    def test_build_root_config_minimal_settings(self):
        cfg = build_root_config('test.files.settings_minimal')
        self.assertEqual(cfg['global'], DEFAULT_SPIDER_GLOBAL_CONFIG)

    def test_build_root_config_overwrite(self):
        cfg = build_root_config('test.files.settings_overwrite')
        for key, val in  DEFAULT_SPIDER_GLOBAL_CONFIG.items():
            if key == 'spider_modules':
                self.assertEqual(cfg['global'][key], ['zzz'])
            else:
                self.assertEqual(cfg['global'][key], val)

    def test_build_spider_config_empty(self):
        class TestSpider(Spider): pass
        root_cfg = build_root_config('test.files.settings_minimal')
        cfg = build_spider_config(TestSpider, root_cfg)
        self.assertEqual(cfg, DEFAULT_SPIDER_GLOBAL_CONFIG)

    def test_build_spider_config_overwrite(self):
        class TestSpider(Spider): pass
        root_cfg = build_root_config('test.files.settings_test_spider')
        cfg = build_spider_config(TestSpider, root_cfg)
        for key, val in  DEFAULT_SPIDER_GLOBAL_CONFIG.items():
            if key == 'spider_modules':
                self.assertEqual(cfg[key], ['zzz'])
            elif key == 'thread_number':
                self.assertEqual(cfg[key], 777)
            else:
                self.assertEqual(cfg[key], val)

    def test_setup_spider_config(self):
        class TestSpider(Spider):
            @classmethod
            def setup_spider_config(cls, config):
                config['foo'] = 'bar'

        root_cfg = build_root_config('test.files.settings_minimal')
        cfg = build_spider_config(TestSpider, root_cfg)
        for key, val in  DEFAULT_SPIDER_GLOBAL_CONFIG.items():
            if key == 'foo':
                self.assertEqual(cfg[key], 'bar')
            else:
                self.assertEqual(cfg[key], val)
