"""
Simple extension system which allows to inherit class
from extension super-classes and cache all extension handlers.
"""

class ExtensionMethods(object):
    """
    Base class with `trigger_extsions` method.

    ExtensionManager metaclass add this base class to list
    of base classes.
    """

    def trigger_extensions(self, point):
        for func in self.extension_handlers[point]:
            func(self)


class ExtensionManager(type):
    def __new__(meta, name, bases, namespace):
        handlers = dict((x, []) for x in namespace['extension_points'])

        for base in bases:
            for key in namespace['extension_points']:
                func = getattr(base, 'extra_%s' % key, None)
                if func:
                    handlers[key].append(func)

        bases += (ExtensionMethods,)

        cls = super(ExtensionManager, meta).__new__(meta, name, bases, namespace)
        cls.extension_handlers = handlers
        return cls
