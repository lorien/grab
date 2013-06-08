from copy import deepcopy
from . import default_config

SPIDER_KEYS = ['QUEUE', 'CACHE', 'PROXY_LIST']

def build_global_config(settings):
    for key in dir(default_config):
        if not hasattr(settings, key):
            setattr(settings, key, deepcopy(getattr(default_config, key)))
    return settings


def build_spider_config(global_config, spider_name):
    spider_settings_key = 'SPIDER_%s' % spider_name.upper()
    spider_config = deepcopy(getattr(global_config, spider_settings_key, {}))
    for key in SPIDER_KEYS:
        if not key in spider_config:
            if hasattr(global_config, key):
                spider_config[key] = deepcopy(getattr(global_config, key))
    return spider_config
