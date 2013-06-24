from abc import ABCMeta, abstractmethod
from datetime import datetime

from ..tools.lxml_tools import clean_html
from ..tools.text import find_number
from .decorator import default, empty, cached, bind_item
from .const import NULL

class Field(object):
    """
    All custom fields should extend this class, and override the get method.
    """

    __metaclass__ = ABCMeta

    def __init__(self, xpath=None, default=NULL, empty_default=NULL,
                 processor=None, **kwargs):
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


class NullField(Field):
    @cached
    @default
    @empty
    @bind_item
    def __get__(self, item, itemtype):
        return self.process(None)


class ItemListField(Field):
    def __init__(self, xpath, item_cls, *args, **kwargs):
        self.item_cls = item_cls
        super(ItemListField, self).__init__(xpath, *args, **kwargs)

    @cached
    @default
    @empty
    @bind_item
    def __get__(self, item, itemtype):
        subitems = []
        for sel in item._selector.select(self.xpath_exp):
            subitem = self.item_cls(sel.node)
            subitem._parse()
            subitems.append(subitem)
        return self.process(subitems)


class IntegerField(Field):
    def __init__(self, *args, **kwargs):
        self.ignore_spaces = kwargs.get('ignore_spaces', False)
        self.ignore_chars = kwargs.get('ignore_chars', None)
        super(IntegerField, self).__init__(*args, **kwargs)

    @cached
    @default
    @empty
    @bind_item
    def __get__(self, item, itemtype):
        value = item._selector.select(self.xpath_exp).text()
        if self.empty_default is not NULL:
            if value == "":
                return self.empty_default
        return find_number(self.process(value), ignore_spaces=self.ignore_spaces,
                           ignore_chars=self.ignore_chars)


class StringField(Field):
    @cached
    @default
    @empty
    @bind_item
    def __get__(self, item, itemtype):
        value = item._selector.select(self.xpath_exp).text()
        return self.process(value)


class HTMLField(Field):
    def __init__(self, *args, **kwargs):
        self.safe_attrs = kwargs.pop('safe_attrs', None)
        super(HTMLField, self).__init__(*args, **kwargs)

    @cached
    @default
    @empty
    @bind_item
    def __get__(self, item, itemtype):
        value = item._selector.select(self.xpath_exp).html()
        if self.safe_attrs is not None:
            return self.process(clean_html(value, output_encoding='unicode'))
        else:
            return self.process(value)


class ChoiceField(Field):
    def __init__(self, *args, **kwargs):
        self.choices = kwargs.pop('choices')
        super(ChoiceField, self).__init__(*args, **kwargs)

    @cached
    @default
    @empty
    @bind_item
    def __get__(self, item, itemtype):
        value = item._selector.select(self.xpath_exp).text()
        try:
            return self.process(self.choices[value])
        except KeyError:
            raise ChoiceFieldError('Unknown choice: %s' % value)


class RegexField(Field):
    def __init__(self, xpath, regex, *args, **kwargs):
        self.regex = regex
        super(RegexField, self).__init__(xpath, *args, **kwargs)

    @cached
    @default
    @bind_item
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
    @bind_item
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
    @bind_item
    def __get__(self, item, itemtype):
        if self.pass_item:
            val = self.func(item, item._selector)
        else:
            val = self.func(item._selector)
        return self.process(val)
