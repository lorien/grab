from copy import deepcopy
from grab.util.default_config import DEFAULT_SPIDER_GLOBAL_CONFIG
import importlib


def update_dict(target, source, overwrite=False):
    for key, val in source.items():
        if key not in target or overwrite:
            target[key] = deepcopy(source[key])
    return target


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
