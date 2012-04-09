from random import choice
from grab.tools.tinyurl import tinyurl
from grab.tools.tinyurl import clck
import logging
import os

MODULES = {}
logger = logging.getLogger('grab.tools.tinyurl')

def load_modules():
    package_dir = os.path.dirname(os.path.realpath(__file__))
    for fname in os.listdir(package_dir):
        if fname.endswith('.py') and not fname.startswith('_'):
            modname = fname[:-3]
            mod = __import__('grab.tools.tinyurl.%s' % modname, 
                             globals(), locals(), ['foo'])
            MODULES[mod.name] = mod


def get_tiny_url(url, service=None, try_count=10):
    for x in xrange(try_count):
        if service is None:
            module = choice(MODULES.values())
        else:
            module = MODULES[service]
        try:
            return module.get_url(url)
        except Exception as ex:
            logger.error('Tinyurl error', exc_info=ex)
    raise Exception('Can not generate short url')


load_modules()
