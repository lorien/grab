from grab.util.py3k_support import *


class DotDict(dict):
    def __getattr__(self, item):
        if hasattr(self, item):
            return self[item]

    def __setattr__(self, key, value):
        self[key] = value


class Chunk(object):
    def __init__(self, xpath, apply_func=None, filter_func=None, one=None):
        self._xpath = xpath
        self._one = one if one is not None else False if filter_func else True
        self._filter_func = filter_func
        self._apply_func = apply_func

    def prepare_element(self, element):
        items = element.xpath(self._xpath)
        if not items:
            return
        if self._one:
            items = items[:1]
        elif self._filter_func:
            items = filter(
                lambda item: self._filter_func(item),
                items
            )
        if self._apply_func and items:
            items = map(
                self._apply_func,
                items
            )
        if items and self._one:
            return list(items)[0]
        else:
            return items


class Structure(object):
    def __init__(self, xpath, *args, **kwargs):
        self._xpath = xpath
        self._args = args
        self._kwargs = kwargs

    def __repr__(self):
        return '<%s %s %s>' % (self._xpath, self._args, self._kwargs)


class TreeInterface(object):
    def __init__(self, tree):
        self._tree = tree

    @property
    def tree(self):
        return self._tree

    def xpath(self, path, default=None, all=False):
        items = self.tree.xpath(path)
        if all:
            return items
        try:
            return items[0]
        except IndexError:
            return default

    def structured_xpath(self, xpath='./', *args, **kwargs):
        def parser(element, structure):
            items = []
            for element in element.xpath(structure._xpath):
                item = DotDict()
                for substructure in structure._args:
                    res = parser(element, substructure)
                    if res:
                        item.update(res[0])
                for key, value in structure._kwargs.items():
                    if isinstance(value, basestring):
                        chunk = Chunk(value, apply_func=lambda item: unicode(item).strip())
                        item[key] = chunk.prepare_element(element)
                    if isinstance(value, Structure):
                        item[key] = parser(element, value)
                    elif isinstance(value, (list, tuple, set)):
                        chunk = Chunk(*value)
                        item[key] = chunk.prepare_element(element)
                    elif isinstance(value, Chunk):
                        item[key] = value.prepare_element(element)
                    else:
                        TypeError('Unknown type for structured type!')
                items.append(item)
            return items

        structure = None
        if isinstance(xpath, basestring):
            structure = Structure(xpath, *args, **kwargs)
        elif isinstance(xpath, Structure):
            structure = xpath
        if structure is None:
            Exception('Unknown type for structured type!')

        return parser(
            self.tree,
            structure
        )
