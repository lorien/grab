import os

from copy import deepcopy
from grab.util import default_config
from grab.util.module import import_string

NULL = object()

# Temporary disabled, spider config are mixed with all global config keys
#SPIDER_KEYS = ['GRAB_QUEUE', 'GRAB_CACHE', 'GRAB_PROXY_LIST', 'GRAB_THREAD_NUMBER',
               #'GRAB_NETWORK_TRY_LIMIT', 'GRAB_TASK_TRY_LIMIT']


def is_dict_interface(obj):
    try:
        _ = obj['o_O']
        list(obj.keys())
    except (TypeError, AttributeError):
        return False
    except Exception:
        return True


class Config(dict):
    def update_with_object(self, obj, only_new_keys=False, allowed_keys=None,
                           only_uppercase_keys=True):
        is_dict = is_dict_interface(obj)
        keys = obj.keys() if is_dict else dir(obj)
        for key in keys:
            if key.isupper() or not only_uppercase_keys:
                if not key.startswith('_'):
                    if not only_new_keys or not key in self:
                        if allowed_keys is None or key in allowed_keys:
                            self[key] = obj[key] if is_dict else getattr(obj, key)

    def update_with_path(self, path, **kwargs):
        obj = import_string(path)
        self.update_with_object(obj, **kwargs)

    def clone(self):
        return Config(deepcopy(self))

    def get(self, key, default=None, deprecated_key=None):
        """
        Get config's value addressed by the `key`.

        You can specify two keys with `key` and `deprecated_key` arguments
        if you are not sure in which format your config is.
        """
        try:
            result = self[key]
        except KeyError:
            if deprecated_key is not None:
                try:
                    result = self[deprecated_key]
                except KeyError:
                    result = default
            else:
                result = default

        return result


def build_root_config(settings_mod_path='settings'):
    config = Config()
    try:
        config.update_with_path(settings_mod_path)
    except ImportError:
        # do not raise exception if settings_mod_path is default
        # and no settings.py file found in current directory
        if (settings_mod_path == 'settings' and
            not os.path.exists(os.path.join(os.path.realpath(os.getcwd()), 'settings.py'))):
            pass
        else:
            raise
    else:
        """
        # Try to read config in modern setting
        if 'GRAB_SPIDER_CONFIG' in config:
            # Need to do that because in ideal way we just need to read only
            # GRAB_SPIDER_CONFIG key and make its values as root of config object
            # BUT we read all keys (deprecated mode), so we need to inject all
            # keys from GRAB_SPIDER_CONFIG into our deprecated global root namespace
            config.update_with_object(deepcopy(config['GRAB_SPIDER_CONFIG']), only_uppercase_keys=False)

        if 'global' in config:
            config['global'] = Config(config['global'])
        else:
            config['global'] = Config()

        config.update_with_object(default_config.default_config, only_new_keys=True)
        config['global'].update_with_object(default_config.default_config, only_new_keys=True)

        return config
        """
        if 'GRAB_SPIDER_CONFIG' in config:
            root_config = Config()
            root_config.update_with_object(deepcopy(config['GRAB_SPIDER_CONFIG']),
                                           only_uppercase_keys=False)
        else:
            root_config = Config()
            root_config['global'] = Config()
            root_config['global'].update_with_object(config)

        # Make root_config['global'] the smart config object
        # because we need to update it
        if 'global' in root_config:
            if not isinstance(root_config['global'], Config):
                root_config['global'] = Config(root_config['global'])
        else:
            root_config['global'] = Config()

        #root_config.update_with_object(default_config.default_config, only_new_keys=True)
        root_config['global'].update_with_object(default_config.default_config, only_new_keys=True)
        
        return root_config

def build_spider_config(spider_class, root_config=None):
    if root_config is None:
        root_config = build_root_config()

    spider_name = spider_class.get_spider_name()
    if spider_name in root_config:
        spider_config = Config(root_config[spider_name])
    else:
        spider_config = Config()

    # Inject keys from global config into spider config
    # Inejct only new keys (that do not exist in spider config)
    spider_config.update_with_object(root_config['global'], only_new_keys=True,
                                     allowed_keys=None, only_uppercase_keys=False)#SPIDER_KEYS)

    # Apply any customization defined in spider class
    # By default this method does nothing
    spider_class.setup_spider_config(spider_config)

    return spider_config
