"""
Simple extension system which allows to inherit class
from extension super-classes and cache all extension handlers.
"""
from copy import copy


class ExtensionSystemError(Exception):
    pass


def trigger_extensions(self, point):
    for func in self.extension_handlers[point]:
        func(self)


def register_extensions(cls):
    """
    Build and cache list of handlers for each extension point.
    """

    if hasattr(cls, 'extension_points'):
        points = cls.extension_points
    else:
        for base in cls.__bases__:
            tmp = getattr(base, 'extension_points', None)
            if tmp is not None:
                points = tmp
                break

    if not points:
        raise ExtensionSystemError('Could not find extension_points attribute '
                                   'nor in class neither in his parents')

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
