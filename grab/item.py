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
from abc import ABCMeta, abstractmethod
from datetime import datetime

from .tools.lxml_tools import get_node_text
from .error import DataNotFound
from .selector import Selector

NULL = object()

class Field(object):
    """
    All custom fields should extend this class, and override the get method.
    """

    __metaclass__ = ABCMeta

    def __init__(self, xpath=None, default=NULL, empty_default=NULL):
        self.xpath_exp = xpath
        self.default = default
        self.empty_default = empty_default

    @abstractmethod
    def __get__(self, obj, objtype):
        pass

    def __set__(self, obj, value):
        obj._cache[self.attr_name] = value


def cached(func):
    def internal(self, item, itemtype):
        if self.attr_name in item._cache:
            return item._cache[self.attr_name]
        else:
            value = func(self, item, itemtype)
            item._cache[self.attr_name] = value
            return value
    return internal


def default(func):
    def internal(self, item, itemtype):
        try:
            value = func(self, item, itemtype)
        except DataNotFound:
            if self.default is not NULL:
                value = self.default
            else:
                raise
        else:
            if self.empty_default is not NULL:
                if not value:
                    value = self.empty_default
        item._cache[self.attr_name] = value
        return value
    return internal


def empty(func):
    def internal(self, item, itemtype):
        if self.xpath_exp is None:
            if self.default is not NULL:
                return self.default
            else:
                return None
        else:
            return func(self, item, itemtype)
    return internal


class IntegerField(Field):
    @cached
    @default
    @empty
    def __get__(self, item, itemtype):
        value = item._selector.select(self.xpath_exp).text()
        if self.empty_default is not NULL:
            if value == "":
                return self.empty_default
        return int(value)


class StringField(Field):
    @cached
    @default
    @empty
    def __get__(self, item, itemtype):
        return item._selector.select(self.xpath_exp).text()


class DateTimeField(Field):
    def __init__(self, xpath, datetime_format, *args, **kwargs):
        self.datetime_format = datetime_format
        super(DateTimeField, self).__init__(xpath, *args, **kwargs)

    @cached
    @default
    def __get__(self, item, itemtype):
        value = item._selector.select(self.xpath_exp).text()
        return datetime.strptime(value, self.datetime_format)


class FuncField(Field):
    def __init__(self, func, pass_item=False, *args, **kwargs):
        self.func = func
        self.pass_item = pass_item
        super(FuncField, self).__init__(*args, **kwargs)

    @cached
    @default
    def __get__(self, item, itemtype):
        if self.pass_item:
            return self.func(item, item._selector)
        else:
            return self.func(item._selector)


def func_field(pass_item=False, *args, **kwargs):
    def inner(func):
        def method_wrapper(self, *args, **kwargs):
            return func(*args, **kwargs)
        if pass_item:
            func2 = func
        else:
            func2 = method_wrapper(func)
        return FuncField(func=func2, pass_item=True, *args, **kwargs)
    return inner


class ItemBuilder(type):
    def __new__(cls, name, base, namespace):
        field_list = []
        for attr in namespace:
            if isinstance(namespace[attr], Field):
                field = namespace[attr]
                field.attr_name = attr
                field_list.append(attr)
                namespace[attr] = field
        namespace['_field_list'] = field_list
        return super(ItemBuilder, cls).__new__(cls, name, base, namespace)


class Item(object):
    __metaclass__ = ItemBuilder

    def __init__(self, tree, grab=None, task=None):
        self._tree = tree
        self._cache = {}
        self._grab = grab
        self._task = task
        self._selector = Selector(self._tree)

    def _parse(self):
        pass

    def _render(self, exclude=()):
        out = []
        for key in self._field_list:
            if not key in exclude:
                out.append('%s: %s' % (key, getattr(self, key)))
        return '\n'.join(out)
