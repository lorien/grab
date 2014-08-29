from grab.const import NULL
from grab.error import DataNotFound

# *******************
# Internal decorators
# *******************


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


def bind_item(func):
    def internal(self, item, itemtype):
        self.item = item
        return func(self, item, itemtype)
    return internal
