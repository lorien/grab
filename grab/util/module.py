"""
The source code of `reraise` and `import_string` was copied from https://github.com/mitsuhiko/werkzeug/blob/master/werkzeug/utils.py
"""
import logging
import sys

from grab.spider.base import Spider
from grab.spider.error import SpiderInternalError
from grab.util.misc import camel_case_to_underscore
from grab.util.py3k_support import *

PY2 = not PY3K
SPIDER_REGISTRY = {}
string_types = (str, unicode)
logger = logging.getLogger('grab.util.module')


def reraise(tp, value, tb=None):
    if sys.version_info < (3,):
        from grab.util import py2x_support
        py2x_support.reraise(tp, value, tb)
    else:
        raise value.with_traceback(tb)


class ImportStringError(ImportError):
    """Provides information about a failed :func:`import_string` attempt."""

    #: String in dotted notation that failed to be imported.
    import_name = None
    #: Wrapped exception.
    exception = None

    def __init__(self, import_name, exception):
        self.import_name = import_name
        self.exception = exception

        msg = (
            'import_string() failed for %r. Possible reasons are:\n\n'
            '- missing __init__.py in a package;\n'
            '- package or module path not included in sys.path;\n'
            '- duplicated package or module name taking precedence in '
            'sys.path;\n'
            '- missing module, class, function or variable;\n\n'
            'Debugged import:\n\n%s\n\n'
            'Original exception:\n\n%s: %s')

        name = ''
        tracked = []
        for part in import_name.replace(':', '.').split('.'):
            name += (name and '.') + part
            imported = import_string(name, silent=True)
            if imported:
                tracked.append((name, getattr(imported, '__file__', None)))
            else:
                track = ['- %r found in %r.' % (n, i) for n, i in tracked]
                track.append('- %r not found.' % name)
                msg = msg % (import_name, '\n'.join(track),
                             exception.__class__.__name__, str(exception))
                break

        ImportError.__init__(self, msg)

    def __repr__(self):
        return '<%s(%r, %r)>' % (self.__class__.__name__, self.import_name,
                                 self.exception)


def import_string(import_name, silent=False):
    """Imports an object based on a string.  This is useful if you want to
    use import paths as endpoints or something similar.  An import path can
    be specified either in dotted notation (``xml.sax.saxutils.escape``)
    or with a colon as object delimiter (``xml.sax.saxutils:escape``).

    If `silent` is True the return value will be `None` if the import fails.

    :param import_name: the dotted name for the object to import.
    :param silent: if set to `True` import errors are ignored and
                   `None` is returned instead.
    :return: imported object
    """

    #XXX: py3 review needed
    assert isinstance(import_name, string_types)
    # force the import name to automatically convert to strings
    import_name = str(import_name)
    try:
        if ':' in import_name:
            module, obj = import_name.split(':', 1)
        elif '.' in import_name:
            module, obj = import_name.rsplit('.', 1)
        else:
            return __import__(import_name)
        # __import__ is not able to handle unicode strings in the fromlist
        # if the module is a package
        if PY2 and isinstance(obj, unicode):
            obj = obj.encode('utf-8')
        if PY3K and isinstance(obj, bytes):
            obj = obj.decode('utf-8')
        try:
            return getattr(__import__(module, None, None, [obj]), obj)
        except (ImportError, AttributeError):
            # support importing modules not yet set up by the parent module
            # (or package for that matter)
            modname = module + '.' + obj
            __import__(modname)
            return sys.modules[modname]
    except ImportError as e:
        if not silent:
            reraise(
                ImportStringError,
                ImportStringError(import_name, e),
                sys.exc_info()[2])


def build_spider_registry(config):
    # TODO: make smart spider class searching
    #for mask in config.SPIDER_LOCATIONS:
        #for path in glob.glob(mask):
            #if path.endswith('.py'):
                #mod_path = path[:-3].replace('/', '.')
                #try:
                    #mod = __import__

    SPIDER_REGISTRY.clear()
    module_mapping = {}

    opt_modules = []
    opt_modules = config['global'].get('spider_modules', deprecated_key='GRAB_SPIDER_MODULES',
                                       default=[])
    #try:
        #opt_modules = config['global']['spider_modules']
    #except KeyError:
        #opt_modules = config.get('GRAB_SPIDER_MODULES', [])

    for path in opt_modules:
        if ':' in path:
            path, cls_name = path.split(':')
        else:
            cls_name = None
        try:
            mod = __import__(path, None, None, ['foo'])
        except ImportError as ex:
            if not path in unicode(ex):
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
                            logger.debug('Module `%s`, found spider `%s` with name `%s`' % (
                                path, val.__name__, spider_name))
                            if spider_name in SPIDER_REGISTRY:
                                raise SpiderInternalError(
                                    'There are two different spiders with the '\
                                    'same name "%s". Modules: %s and %s' % (
                                        spider_name,
                                        SPIDER_REGISTRY[spider_name].__module__,
                                        val.__module__))
                            else:
                                SPIDER_REGISTRY[spider_name] = val
    return SPIDER_REGISTRY


def load_spider_class(config, spider_name):
    if not SPIDER_REGISTRY:
        build_spider_registry(config)
    if not spider_name in SPIDER_REGISTRY:
        raise SpiderInternalError('Unknown spider: %s' % spider_name)
    else:
        return SPIDER_REGISTRY[spider_name]
