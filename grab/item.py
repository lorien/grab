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
import logging

from .tools.lxml_tools import get_node_text
from .error import DataNotFound
from .selector import Selector

NULL = object()

class Field(object):
    """
    All custom fields should extend this class, and override the get method.
    """

    __metaclass__ = ABCMeta

    def __init__(self, xpath=None, default=NULL, empty_default=NULL,
                 processor=None):
        self.xpath_exp = xpath
        self.default = default
        self.empty_default = empty_default
        self.processor = processor

    @abstractmethod
    def __get__(self, obj, objtype):
        pass

    def __set__(self, obj, value):
        obj._cache[self.attr_name] = value

    def process(self, value):
        if self.processor:
            return self.processor(value)
        else:
            return value


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


def processor(func):
    def internal(self, item, itemtype):
        value = func(self, item, itemtype)
        if self.processor:
            return self.processor(value)
        else:
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


class NullField(Field):
    @cached
    @default
    @empty
    def __get__(self, item, itemtype):
        return self.process(None)


class ItemListField(Field):
    def __init__(self, xpath, item_cls, *args, **kwargs):
        self.item_cls = item_cls
        super(ItemListField, self).__init__(xpath, *args, **kwargs)

    @cached
    @default
    @empty
    def __get__(self, item, itemtype):
        subitems = []
        for sel in item._selector.select(self.xpath_exp):
            subitem = self.item_cls(sel.node)
            subitem._parse()
            subitems.append(subitem)
        return self.process(subitems)


class IntegerField(Field):
    @cached
    @default
    @empty
    def __get__(self, item, itemtype):
        value = item._selector.select(self.xpath_exp).text()
        if self.empty_default is not NULL:
            if value == "":
                return self.empty_default
        return int(self.process(value))


class StringField(Field):
    @cached
    @default
    @empty
    def __get__(self, item, itemtype):
        value = item._selector.select(self.xpath_exp).text()
        return self.process(value)


class RegexField(Field):
    def __init__(self, xpath, regex, *args, **kwargs):
        self.regex = regex
        super(RegexField, self).__init__(xpath, *args, **kwargs)

    @cached
    @default
    def __get__(self, item, itemtype):
        value = item._selector.select(self.xpath_exp).text()
        match = self.regex.search(value)
        if match:
            return self.process(match.group(1))
        else:
            raise DataNotFound('Could not find regex')


class DateTimeField(Field):
    def __init__(self, xpath, datetime_format, *args, **kwargs):
        self.datetime_format = datetime_format
        super(DateTimeField, self).__init__(xpath, *args, **kwargs)

    @cached
    @default
    def __get__(self, item, itemtype):
        value = item._selector.select(self.xpath_exp).text()
        return datetime.strptime(self.process(value),
                                 self.datetime_format)


class FuncField(Field):
    def __init__(self, func, pass_item=False, *args, **kwargs):
        self.func = func
        self.pass_item = pass_item
        super(FuncField, self).__init__(*args, **kwargs)

    @cached
    @default
    def __get__(self, item, itemtype):
        if self.pass_item:
            val = self.func(item, item._selector)
        else:
            val = self.func(item._selector)
        return self.process(val)


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
        fields = {}
        for attr in namespace:
            if isinstance(namespace[attr], Field):
                field = namespace[attr]
                field.attr_name = attr
                namespace[attr] = field
                fields[attr] = namespace[attr]
        namespace['_fields'] = fields
        return super(ItemBuilder, cls).__new__(cls, name, base, namespace)


class Item(object):
    __metaclass__ = ItemBuilder

    def __init__(self, tree, grab=None):
        self._tree = tree
        self._cache = {}
        self._grab = grab
        self._selector = Selector(self._tree)

    @classmethod
    def find(cls, root, **kwargs):
        for count, sel in enumerate(root.select(cls.Meta.find_selector)):
            item = cls(sel.node)
            item._parse(**kwargs)
            item._position = count
            yield item


    @classmethod
    def find_one(cls, *args, **kwargs):
        return list(cls.find(*args, **kwargs))[0]

    def _parse(self, url=None, **kwargs):
        pass

    def _render(self, exclude=(), prefix=''):
        out = []
        for key, field in self._fields.items():
            if not key in exclude:
                if not isinstance(field, ItemListField):
                    out.append(prefix + '%s: %s' % (key, getattr(self, key)))
        for key, field in self._fields.items():
            if not key in exclude:
                if isinstance(field, ItemListField):
                    child_out = []
                    for item in getattr(self, key):
                        child_out.append(item._render(prefix=prefix + '  '))
                    out.append('\n'.join(child_out))
        out.append(prefix + '---')
        return '\n'.join(out)

    def update_object(self, obj, keys):
        for key in keys:
            setattr(obj, key, getattr(self, key))

    def update_dict(self, obj, keys):
        for key in keys:
            obj[key] = getattr(self, key)

    def get_dict(self, keys):
        obj = {}
        for key in keys:
            obj[key] = getattr(self, key)
        return obj
