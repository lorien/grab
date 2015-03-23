import os

from copy import deepcopy
from grab.util.default_config import DEFAULT_SPIDER_GLOBAL_CONFIG
import importlib

NULL = object()

def update_dict(target, source, overwrite=False):
    for key, val in source.items():
        if key not in target or overwrite:
            target[key] = deepcopy(source[key])


class Config(dict):
    def update_with_object(self, obj, only_new_keys=False, allowed_keys=None):
        is_dict = is_dict_interface(obj)
        keys = obj.keys() if is_dict else dir(obj)
        for key in keys:
            if not key.startswith('_'):
                if not only_new_keys or key not in self:
                    if allowed_keys is None or key in allowed_keys:
                        self[key] = obj[key] if is_dict else getattr(obj, key)

    def update_with_path(self, path, **kwargs):
        obj = importlib.import_module(path)
        self.update_with_object(obj, **kwargs)

    def clone(self):
        return Config(deepcopy(self))

    def get(self, key, default=None):
        """Get config's value addressed by the `key`."""
        try:
            return self[key]
        except KeyError:
            return default


def build_root_config(settings_mod_path):
    module = importlib.import_module(settings_mod_path)
    config = module.GRAB_SPIDER_CONFIG
    if not 'global' in config:
        config['global'] = {}
    update_dict(config['global'], DEFAULT_SPIDER_GLOBAL_CONFIG,
                overwrite=False)
    return config


def build_spider_config(spider_class, root_config):
    spider_name = spider_class.get_spider_name()
    spider_config = deepcopy(root_config.get(spider_name, {}))
    update_dict(spider_config, root_config['global'], overwrite=False)
    spider_class.setup_spider_config(spider_config)
    return spider_config
