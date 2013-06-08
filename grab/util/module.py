import logging

from grab.spider.base import Spider
from grab.spider.error import SpiderInternalError
from grab.util.misc import camel_case_to_underscore

SPIDER_REGISTRY = {}

logger = logging.getLogger('grab.util.module')

def build_spider_registry(config):
    # TODO: make smart spider class searching
    #for mask in config.SPIDER_LOCATIONS:
        #for path in glob.glob(mask):
            #if path.endswith('.py'):
                #mod_path = path[:-3].replace('/', '.')
                #try:
                    #mod = __import__
    for path in config.SPIDER_MODULES:
        try:
            mod = __import__(path, None, None, ['foo'])
        except ImportError:
            pass
        else:
            for key in dir(mod):
                val = getattr(mod, key)
                if isinstance(val, type) and issubclass(val, Spider):
                    if hasattr(val, 'spider_name'):
                        spider_name = getattr(val, 'spider_name')
                    else:
                        spider_name = camel_case_to_underscore(val.__name__)
                    logger.debug('Module `%s`, found spider `%s` with name `%s`' % (
                        path, val.__name__, spider_name))
                    if spider_name in SPIDER_REGISTRY:
                        raise SpiderInternalError('There are two different spiders with the '\
                                                'same name "%s" % spider_name')
                    else:
                        SPIDER_REGISTRY[spider_name] = val


def load_spider_class(config, spider_name):
    if not SPIDER_REGISTRY:
        build_spider_registry(config)
    if not spider_name in SPIDER_REGISTRY:
        raise SpiderInternalError('Unknown spider: %s' % spider_name)
    else:
        return SPIDER_REGISTRY[spider_name]
