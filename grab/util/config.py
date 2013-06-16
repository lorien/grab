from copy import deepcopy
from grab.util import default_config
from grab.util.module import import_string

SPIDER_KEYS = ['QUEUE', 'CACHE', 'PROXY_LIST', 'THREAD_NUMBER',
               'NETWORK_TRY_LIMIT', 'TASK_TRY_LIMIT']

def is_dict_interface(obj):
    try:
        obj['o_O']
        obj.keys()
    except (TypeError, AttributeError):
        return False
    except Exception:
        return True


class Config(dict):
    def update_with_object(self, obj, only_new_keys=False, allowed_keys=None):
        is_dict = is_dict_interface(obj)
        keys = obj.keys() if is_dict else dir(obj)
        for key in keys:
            if key.isupper():
                if not only_new_keys or not key in self:
                    if allowed_keys is None or key in allowed_keys:
                        self[key] = obj[key] if is_dict else getattr(obj, key)

    def update_with_path(self, path, **kwargs):
        obj = import_string(path)
        self.update_with_object(obj, **kwargs)

    def clone(self):
        return Config(deepcopy(self))

    def getint(self, key):
        return int(self[key])


def build_global_config(settings_mod_path='settings'):
    config = Config()
    config.update_with_path(settings_mod_path)
    config.update_with_object(default_config.default_config, only_new_keys=True)
    return config


def build_spider_config(spider_name, global_config=None):
    if global_config is None:
        global_config = build_global_config()
    spider_settings_key = 'SPIDER_CONFIG_%s' % spider_name.upper()
    spider_config = Config(global_config.get(spider_settings_key, {}))
    spider_config.update_with_object(global_config, only_new_keys=True,
                                     allowed_keys=SPIDER_KEYS)
    return spider_config
