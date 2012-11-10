"""
Simple extension system which allows to inherit class
from extension super-classes and cache all extension handlers.
"""
from copy import copy

class ExtensionSystemError(object):
    pass


class ExtensionMethods(object):
    """
    Base class with `trigger_extsions` method.

    ExtensionManager metaclass add this base class to list
    of base classes.
    """

    def trigger_extensions(self, point):
        for func in self.extension_handlers[point]:
            func(self)

def trigger_extensions(self, point):
    for func in self.extension_handlers[point]:
        func(self)


class ExtensionManager(type):
    def __new__(meta, name, bases, namespace):
        if 'extension_points' in namespace:
            points = namespace['extension_points']
        else:
            for base in bases:
                tmp = getattr(base, 'extension_points', None)
                if tmp is not None:
                    points = tmp
                    break

        if not points:
            raise ExtensionSystemError('Could not find extension_points attribute nor in class neither in his parents')

        if not 'extension_points' in namespace:
            namespace['extension_points'] = copy(points)
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


def register_extensions(cls):
    if hasattr(cls, 'extension_points'):
        points = cls.extension_points
    else:
        for base in cls.__bases__:
            tmp = getattr(base, 'extension_points', None)
            if tmp is not None:
                points = tmp
                break

    if not points:
        raise ExtensionSystemError('Could not find extension_points attribute nor in class neither in his parents')

    if not hasattr(cls, 'extension_points'):
        cls.extension_points = copy(points)
    handlers = dict((x, []) for x in cls.extension_points)

    for base in cls.__bases__:
        for key in cls.extension_points:
            func = getattr(base, 'extra_%s' % key, None)
            if func:
                handlers[key].append(func)

    cls.extension_handlers = handlers
    cls.trigger_extensions = trigger_extensions
