# coding: utf-8
"""
Items allow you get convenient access to different parts of document
through builtin the lxml extension, and make your code more readable.

Usage example:

    >>> class SomeStructure(Item):
    >>>     id = IntegerField('//path/to/@id')
    >>>     name = StringField('//path/to/name')
    >>>     date = DateTimeField('//path/to/@datetime', '%Y-%m-%d %H:%M:%S')

    >>> grab = Grab()
    >>> grab.go('http://exmaple.com')

    >>> structure = SomeStructure(grab.tree)

    >>> structure.id
    1
    >>> structure.name
    "Name of Element"
    >>> structure.date
    datetime.datetime(...)

"""
from __future__ import absolute_import
import collections

from .field import (StringField, IntegerField, DateTimeField,
                    HTMLField, FuncField, NullField, ChoiceField,
                    RegexField, ItemListField)
from .item import Item
from ..error import GrabMisuseError

def func_field(*args, **kwargs):
    if not kwargs and len(args) == 1 and isinstance(args[0], collections.Callable):
        raise GrabMisuseError('It seems that you forgot to "call" the func_field decorator. Use "@func_field()" instead "func_field".')
    def wrapper(func):
        kwargs['pass_item'] = True
        return FuncField(func=func, *args, **kwargs)
    return wrapper
