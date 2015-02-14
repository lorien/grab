from abc import ABCMeta, abstractmethod
from datetime import datetime
try:
    from cdecimal import Decimal
except ImportError:
    from decimal import Decimal

from grab.tools.lxml_tools import clean_html
from grab.tools.text import find_number, drop_space
from grab.item.decorator import default, empty, cached, bind_item
from grab.const import NULL
from grab.item.error import ChoiceFieldError

metaclass_ABCMeta = ABCMeta('metaclass_ABCMeta', (object, ), {})


class Field(metaclass_ABCMeta):
    """
    All custom fields should extend this class, and override the get method.
    """

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
            subitems.append(subitem)
        return self.process(subitems)


class IntegerField(Field):
    def __init__(self, *args, **kwargs):
        self.find_number = kwargs.get('find_number', False)
        self.ignore_spaces = kwargs.get('ignore_spaces', False)
        self.ignore_chars = kwargs.get('ignore_chars', None)
        self.multiple = kwargs.get('multiple', False)
        super(IntegerField, self).__init__(*args, **kwargs)

    def get_raw_values(self, item):
        return item._selector.select(self.xpath_exp).text_list()

    def get_raw_value(self, item):
        return item._selector.select(self.xpath_exp).text()

    @cached
    @default
    @empty
    @bind_item
    def __get__(self, item, itemtype):
        if self.multiple:
            result = []
            for raw_value in self.get_raw_values(item):
                result.append(self.process_raw_value(raw_value))
            return result
        else:
            raw_value = self.get_raw_value(item)
            return self.process_raw_value(raw_value)

    def process_raw_value(self, value):
        if self.empty_default is not NULL:
            if value == "":
                return self.empty_default

        if self.find_number or self.ignore_spaces or self.ignore_chars:
            return find_number(self.process(value),
                               ignore_spaces=self.ignore_spaces,
                               ignore_chars=self.ignore_chars)
        else:
            # TODO: process ignore_chars and ignore_spaces in this case too
            if self.ignore_chars:
                for char in ignore_chars:
                    value = value.replace(char, '')
            if self.ignore_spaces:
                value = drop_space(value)
            return int(self.process(value).strip())


class DecimalField(Field):
    def __init__(self, *args, **kwargs):
        self.multiple = kwargs.get('multiple', False)
        super(DecimalField, self).__init__(*args, **kwargs)

    def get_raw_values(self, item):
        return item._selector.select(self.xpath_exp).text_list()

    def get_raw_value(self, item):
        return item._selector.select(self.xpath_exp).text()

    @cached
    @default
    @empty
    @bind_item
    def __get__(self, item, itemtype):
        if self.multiple:
            result = []
            for raw_value in self.get_raw_values(item):
                result.append(self.process_raw_value(raw_value))
            return result
        else:
            raw_value = self.get_raw_value(item)
            return self.process_raw_value(raw_value)

    def process_raw_value(self, value):
        if self.empty_default is not NULL:
            if value == "":
                return self.empty_default

        return Decimal(self.process(value).strip())


class StringField(Field):
    def __init__(self, *args, **kwargs):
        self.normalize_space = kwargs.pop('normalize_space', True)
        self.multiple = kwargs.get('multiple', False)
        super(StringField, self).__init__(*args, **kwargs)

    @cached
    @default
    @empty
    @bind_item
    def __get__(self, item, itemtype):
        #value = item._selector.select(self.xpath_exp)\
                    #.text(normalize_space=self.normalize_space)
        #return self.process(value)

        if self.multiple:
            result = []
            for raw_value in self.get_raw_values(item):
                result.append(self.process_raw_value(raw_value))
            return result
        else:
            raw_value = self.get_raw_value(item)
            return self.process_raw_value(raw_value)

    def process_raw_value(self, value):
        return self.process(value)

    def get_raw_values(self, item):
        return item._selector.select(self.xpath_exp).text_list()

    def get_raw_value(self, item):
        return item._selector.select(self.xpath_exp).text()


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
        clean_value = self.process(value)
        try:
            return self.choices[clean_value]
        except KeyError:
            raise ChoiceFieldError('Unknown choice: %s' % clean_value)


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
    def __init__(self, xpath, datetime_format='Y-m-d', *args, **kwargs):
        self.datetime_format = datetime_format
        super(DateTimeField, self).__init__(xpath, *args, **kwargs)

    @cached
    @default
    @bind_item
    def __get__(self, item, itemtype):
        value = item._selector.select(self.xpath_exp).text()
        return datetime.strptime(self.process(value),
                                 self.datetime_format)


class DateField(Field):
    def __init__(self, xpath, date_format='Y-m-d', *args, **kwargs):
        self.date_format = date_format
        super(DateField, self).__init__(xpath, *args, **kwargs)

    @cached
    @default
    @bind_item
    def __get__(self, item, itemtype):
        value = item._selector.select(self.xpath_exp).text()
        return datetime.strptime(self.process(value),
                                 self.date_format).date()


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


class BooleanField(Field):
    @cached
    @default
    @bind_item
    def __get__(self, item, itemtype):
        return item._selector.select(self.xpath_exp).exists()
