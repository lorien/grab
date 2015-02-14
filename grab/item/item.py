import logging

from grab.item.field import Field, ItemListField
from grab.selector import XpathSelector
from grab.error import GrabMisuseError
from grab.document import Document

logger = logging.getLogger('grab.item.item')


class ItemBuilder(type):
    def __new__(cls, name, bases, namespace):
        fields = {}

        for attr in namespace:
            if isinstance(namespace[attr], Field):
                field = namespace[attr]
                field.attr_name = attr
                namespace[attr] = field
                fields[attr] = field

        for base in reversed(bases):
            if hasattr(base, '_fields'):
                for attr, field in base._fields.items():
                    if not attr in namespace:
                        fields[attr] = field

        namespace['_fields'] = fields

        cls = super(ItemBuilder, cls).__new__(cls, name, bases, namespace)
        return cls


ItemBuilderMetaClass = ItemBuilder('ItemBuilderMetaClass', (object, ), {})


class Item(ItemBuilderMetaClass):
    def __init__(self, tree, selector_type='xpath', **kwargs):
        self._cache = {}
        self._meta = kwargs
        self._selector = Item._build_selector(tree, selector_type)

    @classmethod
    def _build_selector(cls, tree, selector_type):
        if selector_type == 'xpath':
            return XpathSelector(tree)
        else:
            raise GrabMisuseError('Unknown selector type: %s' % selector_type)

    @classmethod
    def _get_selector_type(cls, default='xpath'):
        return getattr(cls.Meta, 'selector_type', default)

    @classmethod
    def find(cls, tree, **kwargs):
        # Backward Compatibility
        # First implementations of Item module required
        # `grab.doc` to be passed in `tree` option
        if isinstance(tree, Document):
            tree = tree.grab.tree

        selector_type = cls._get_selector_type(kwargs.pop('selector_type',
                                                          'xpath'))
        root_selector = Item._build_selector(tree, selector_type)

        fallback_find_query = getattr(cls.Meta, 'find_selector', '.')
        if hasattr(cls.Meta, 'find_selector'):
            logger.error('Meta.find_selector attribute is deprecated. Please '
                         'use Meta.find_query attribute instead.')
        find_query = getattr(cls.Meta, 'find_query', fallback_find_query)

        for count, sel in enumerate(root_selector.select(find_query)):
            item = cls(sel.node, selector_type=selector_type, **kwargs)
            item._position = count
            yield item

    @classmethod
    def find_one(cls, *args, **kwargs):
        return list(cls.find(*args, **kwargs))[0]

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
        Also calculate all fields as after deserialization
        it will not be possible to calculate any field.
        """
        for key in self._fields.keys():
            # trigger fields' content calculation
            getattr(self, key)
        state = self.__dict__.copy()
        state['_selector'] = None
        return state

    @classmethod
    def extract_document_data(cls, grab):
        """
        Extract document data from grab object in format that is
        suitable to pass to `cls` Item constructor.
        """

        sel_type = cls._get_selector_type()
        if sel_type == 'xpath':
            return grab.tree
        elif sel_type == 'json':
            return grab.response.json
        else:
            raise GrabMisuseError('Unknown selector type: %s' % sel_type)
