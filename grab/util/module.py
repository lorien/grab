import logging
import six

from grab.spider.base import Spider
from grab.spider.error import SpiderInternalError
from grab.util.config import build_root_config, build_spider_config

SPIDER_REGISTRY = {}
logger = logging.getLogger('grab.util.module')


def build_spider_registry(config):
    SPIDER_REGISTRY.clear()

    opt_modules = []
    opt_modules = config['global'].get('spider_modules', [])

    for path in opt_modules:
        if ':' in path:
            path, cls_name = path.split(':')
        else:
            cls_name = None
        try:
            mod = __import__(path, None, None, ['foo'])
        except ImportError as ex:
            if path not in six.text_type(ex):
                logging.error('', exc_info=ex)
        else:
            for key in dir(mod):
                if key == 'Spider':
                    continue
                if cls_name is None or key == cls_name:
                    val = getattr(mod, key)
                    if isinstance(val, type) and issubclass(val, Spider):
                        if val.Meta.abstract:
                            pass
                        else:
                            spider_name = val.get_spider_name()
                            logger.debug(
                                'Module `%s`, found spider `%s` '
                                'with name `%s`' % (
                                    path, val.__name__, spider_name))
                            if spider_name in SPIDER_REGISTRY:
                                mod = SPIDER_REGISTRY[spider_name].__module__
                                raise SpiderInternalError(
                                    'There are two different spiders with '
                                    'the same name "%s". '
                                    'Modules: %s and %s' % (
                                        spider_name, mod, val.__module__))
                            else:
                                SPIDER_REGISTRY[spider_name] = val
    return SPIDER_REGISTRY


def load_spider_class(config, spider_name):
    if not SPIDER_REGISTRY:
        build_spider_registry(config)
    if spider_name not in SPIDER_REGISTRY:
        raise SpiderInternalError('Unknown spider: %s' % spider_name)
    else:
        return SPIDER_REGISTRY[spider_name]


def build_spider_instance(cls, settings_module, **kwargs):
    root_config = build_root_config(settings_module)
    spider_config = build_spider_config(cls, root_config)
    return cls(config=spider_config)
