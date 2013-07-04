from .field import Field, ItemListField
from ..selector import XpathSelector

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

    def __init__(self, tree, **kwargs):
        self._cache = {}
        self._meta = kwargs
        self._selector = XpathSelector(tree)

    @classmethod
    def find(cls, root, **kwargs):
        for count, sel in enumerate(root.select(getattr(cls.Meta, 'find_selector', '.'))):
            item = cls(sel.node, **kwargs)
            #item._parse(**kwargs)
            item._position = count
            yield item


    @classmethod
    def find_one(cls, *args, **kwargs):
        return list(cls.find(*args, **kwargs))[0]

    #def _parse(self, url=None, **kwargs):
        #pass

    def _render(self, exclude=(), prefix=''):
        out = []
        for key, field in self._fields.items():
            if not key in exclude:
                if not isinstance(field, ItemListField):
                    out.append(prefix + '%s: %s' % (key, getattr(self, key)))
        for key, field in self._fields.items():
            if not key in exclude:
                if isinstance(field, ItemListField):
                    out.append(prefix + key + ':')
                    child_out = []
                    for item in getattr(self, key):
                        child_out.append(item._render(prefix=prefix + '  '))
                    out.append('\n'.join(child_out))
        out.append(prefix + '---')
        return '\n'.join(out)

    def update_object(self, obj, keys):
        for key in keys:
            setattr(obj, key, getattr(self, key))

    def update_dict(self, dct, keys):
        for key in keys:
            dct[key] = getattr(self, key)

    def get_dict(self, keys=None):
        if keys is None:
            keys = self._fields.keys()
        dct = {}
        for key in keys:
            dct[key] = getattr(self, key)
        return dct

    @classmethod
    def get_function(cls, key):
        """
        Return standalone function which was used to build FuncField field.
        """
        field = cls._fields[key]
        if field.pass_item:
            def func_wrapper(*args, **kwargs):
                return field.func(None, *args, **kwargs)
            return func_wrapper
        else:
            return field.func

    def __getstate__(self):
        """
        Delete `self._selector` object because it is not
        possible to picklize lxml-tree.
        Also calculate all fields becuase after deserialization
        it will not be possible to calculate any field.
        """
        for key in self._fields.keys():
            # trigger fields' content calcualation
            getattr(self, key)
        state = self.__dict__.copy()
        state['_selector'] = None
        return state
