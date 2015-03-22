from unittest import TestCase
"""
import sys
import os
from copy import deepcopy

from test.util import TMP_DIR
from grab.util import default_config
from grab.spider import Spider
"""
from grab.util.config import (Config, build_root_config, build_spider_config,
                              is_dict_interface)


"""
class SomeSettings(object):
    VAR1 = 'val1'
    VAR2 = 'val2'
    trash = 'xxx'


SOME_DICT = {'global': {'var1': 'val1', 'var2': 'val2', 'trash': 'xxx'}}
SETTINGS_COUNTER = 1


def setup_settings_file(settings):
    global SETTINGS_COUNTER

    modname = 'grab_test_settings_%d' % SETTINGS_COUNTER
    SETTINGS_COUNTER += 1

    if TMP_DIR not in sys.path:
        sys.path.append(TMP_DIR)
    with open(os.path.join(TMP_DIR, modname + '.py'), 'w') as out:
        out.write(str(settings))
    sys.path.append(TMP_DIR)
    return modname


def keep_default_config(func):
    def wrapper(*args, **kwargs):
        original_default_config = deepcopy(default_config.default_config)
        try:
            return func(*args, **kwargs)
        finally:
            default_config.default_config = original_default_config
    return wrapper


"""
class ConfigTestCase(TestCase):
    """
    def test_config_constructor(self):
        config = Config()
        self.assertEqual(len(config.keys()), 0)

        config = Config({'foo': 'bar'})
        self.assertEqual(len(config.keys()), 1)
        self.assertEqual(config['foo'], 'bar')

    def test_clone(self):
        config = Config({'foo': 'bar'})
        config2 = config.clone()
        self.assertEqual(config, config2)
        self.assertFalse(config is config2)

    def test_update_with_object(self):
        config = Config()
        obj = SomeSettings()
        config.update_with_object(obj)
        self.assertEqual(config, {'var1': 'val1', 'var2': 'val2'})

    def test_update_with_object_new_keys(self):
        config = Config({'var1': 'original'})
        obj = SomeSettings()
        config.update_with_object(obj, only_new_keys=True)
        self.assertEqual(config, {'var1': 'original', 'var2': 'val2'})

    def test_update_with_object_allowed_keys(self):
        config = Config({'var1': 'original'})
        obj = SomeSettings()
        config.update_with_object(obj, allowed_keys=['var1'])
        self.assertEqual(config, {'var1': 'val1'})

    def test_update_with_dict(self):
        config = Config()
        config.update_with_object(SOME_DICT)
        self.assertEqual(config, {'var1': 'val1', 'var2': 'val2'})

    def test_update_with_dict_new_keys(self):
        config = Config({'var1': 'original'})
        config.update_with_object(SOME_DICT, only_new_keys=True)
        self.assertEqual(config, {'var1': 'original', 'var2': 'val2'})

    def test_update_with_dict_allowed_keys(self):
        config = Config({'var1': 'original'})
        config.update_with_object(SOME_DICT, allowed_keys=['var1'])
        self.assertEqual(config, {'var1': 'val1'})

    def test_update_with_path(self):
        modname = setup_settings_file(SOME_DICT)
        config = Config()
        config.update_with_path(modname)
        self.assertEqual(config, {'var1': 'val1', 'var2': 'val2'})

    def test_update_with_path_new_keys(self):
        modname = setup_settings_file(SOME_DICT)
        config = Config({'global': {'var1': 'original'}})
        config.update_with_path(modname, only_new_keys=True)
        self.assertEqual(config,
                         {'global': {'var1': 'original', 'var2': 'val2'}})

    def test_update_with_path_allowed_keys(self):
        modname = setup_settings_file(SOME_DICT)
        config = Config()
        config.update_with_path(modname, allowed_keys=['var1'])
        self.assertEqual(config, {'var1': 'val1'})

    @keep_default_config
    def test_build_root_config1(self):
        modname = setup_settings_file({'CACHE': {'backend': 'redis'}})
        default_config.default_config = {}
        config = build_root_config(modname)
        self.assertEqual(config['CACHE'], {'backend': 'redis'})

    @keep_default_config
    def test_build_root_config2(self):
        modname = setup_settings_file(
            {'global': {'cache': {'backend': 'redis'}}})
        default_config.default_config = {'cache': {'backend': 'mysql'}}
        config = build_root_config(modname)
        self.assertEqual(config['global']['cache'], {'backend': 'redis'})

    @keep_default_config
    def test_build_root_config3(self):
        modname = setup_settings_file({})
        default_config.default_config = {'cache': {'backend': 'mysql'}}
        config = build_root_config(modname)
        self.assertEqual(config['global']['cache'], {'backend': 'mysql'})

    @keep_default_config
    def test_build_spider_config1(self):
        class FooSpider(Spider):
            pass

        modname = setup_settings_file({})
        default_config.default_config = {
            'cache': {'backend': 'mysql'},
            'var1': 'val1',
        }
        config = build_root_config(modname)
        spider_config = build_spider_config(FooSpider, config)
        self.assertEqual(spider_config['cache'], {'backend': 'mysql'})
    """
    def test_is_dict_interface(self):
        self.assertTrue(is_dict_interface({}))
        self.assertFalse(is_dict_interface(1))
        self.assertFalse(is_dict_interface([]))
        self.assertFalse(is_dict_interface('asfasdf'))
