"""
Selector module provides high usability interface to lxml tree
"""
import logging
import time
try:
    from pyquery import PyQuery
except ImportError:
    pass
from abc import ABCMeta, abstractmethod

from grab.tools.lxml_tools import get_node_text, render_html
from grab.tools.text import find_number, normalize_space as normalize_space_func
from grab.error import GrabMisuseError, DataNotFound, warn
from grab.tools import rex as rex_tools
from grab.tools.text import normalize_space
from grab.tools.html import decode_entities
import grab.base
from grab.const import NULL
from grab.util.py3k_support import *

__all__ = ['Selector', 'TextSelector', 'XpathSelector', 'PyquerySelector',
           'KitSelector']
XPATH_CACHE = {}
logger = logging.getLogger('grab.selector.selector')

metaclass_ABCMeta = ABCMeta('metaclass_ABCMeta', (object, ), {})

class SelectorList(object):
    __slots__ = ('selector_list', 'origin_selector_class', 'origin_query')

    def __init__(self, selector_list, origin_selector_class, origin_query):
        self.selector_list = selector_list
        self.origin_selector_class = origin_selector_class
        self.origin_query = origin_query

    def __getitem__(self, x):
        return self.selector_list[x]

    def __len__(self):
        return self.count()

    def count(self):
        return len(self.selector_list)

    def one(self, default=NULL):
        try:
            return self.selector_list[0]
        except IndexError:
            if default is NULL:
                m = 'Could not get first item for %s query of class %s'\
                    % (self.origin_query, self.origin_selector_class.__name__)
                raise DataNotFound(m)
            else:
                return default

    def node(self, default=NULL):
        try:
            return self.one().node
        except IndexError:
            if default is NULL:
                m = 'Could not get first item for %s query of class %s'\
                    % (self.origin_query, self.origin_selector_class.__name__)
                raise DataNotFound(m)
            else:
                return default

    def text(self, default=NULL, smart=False, normalize_space=True):
        try:
            sel = self.one()
        except IndexError:
            if default is NULL:
                raise
            else:
                return default
        else:
            return sel.text(smart=smart, normalize_space=normalize_space)

    def text_list(self, smart=False, normalize_space=True):
        result_list = []
        for item in self.selector_list:
            result_list.append(item.text())
        return result_list

    def html(self, default=NULL, encoding='unicode'):
        try:
            sel = self.one()
        except IndexError:
            if default is NULL:
                raise
            else:
                return default
        else:
            return sel.html(encoding=encoding)

    def number(self, default=NULL, ignore_spaces=False,
               smart=False, make_int=True):
        """
        Find number in normalized text of node which matches the given xpath.
        """

        try:
            sel = self.one()
        except IndexError:
            if default is NULL:
                raise
            else:
                return default
        else:
            return sel.number(ignore_spaces=ignore_spaces, smart=smart,
                              default=default, make_int=make_int)

    def exists(self):
        """
        Return True if selector list is not empty.
        """

        return len(self.selector_list) > 0

    def assert_exists(self):
        """
        Return True if selector list is not empty.
        """

        if not self.exists():
            raise DataNotFound(u'Node does not exists, query: %s, query type: %s' % (
                self.origin_query, self.origin_selector_class.__name__))

    def attr(self, key, default=NULL):
        try:
            sel = self.one()
        except IndexError:
            if default is NULL:
                raise
            else:
                return default
        else:
            return sel.attr(key, default=default)

    def attr_list(self, key, default=NULL):
        result_list = []
        for item in self.selector_list:
            result_list.append(item.attr(key, default=default))
        return result_list

    def rex(self, regexp, flags=0, byte=False, default=NULL):
        try:
            sel = self.one()
        except IndexError:
            if default is NULL:
                raise
            else:
                return default
        else:
            return self.one().rex(regexp, flags=flags, byte=byte)

    def node_list(self):
        return [x.node for x in self.selector_list]

    def select(self, query):
        result = SelectorList([], self.origin_selector_class,
                              self.origin_query + ' + ' + query)
        for count, selector in enumerate(self.selector_list):
            result.selector_list.extend(selector.select(query))
        return result


class BaseSelector(metaclass_ABCMeta):
    __slots__ = ('node',)

    def __init__(self, node):
        self.node = node

    def select(self, query):
        start = time.time()
        selector_list = self.wrap_node_list(self.process_query(query), query)
        total = time.time() - start
        grab.base.GLOBAL_STATE['selector_time'] += total
        return selector_list

    def wrap_node_list(self, nodes, query):
        selector_list = []
        for node in nodes:
            if isinstance(node, basestring):
                selector_list.append(TextSelector(node))
            else:
                selector_list.append(self.__class__(node))
        return SelectorList(selector_list, self.__class__, query)

    @abstractmethod
    def html(self):
        raise NotImplementedError

    @abstractmethod
    def attr(self):
        raise NotImplementedError

    @abstractmethod
    def text(self):
        raise NotImplementedError

    def number(self, default=NULL, ignore_spaces=False,
               smart=False, make_int=True):
        try:
            return find_number(self.text(smart=smart),
                               ignore_spaces=ignore_spaces,
                               make_int=make_int)
        except IndexError:
            if default is NULL:
                raise
            else:
                return default

    def rex(self, regexp, flags=0, byte=False):
        norm_regexp = rex_tools.normalize_regexp(regexp, flags)
        matches = list(norm_regexp.finditer(self.html()))
        return RexResultList(matches, source_rex=norm_regexp)


class LxmlNodeBaseSelector(BaseSelector):
    __slots__ = ()

    def html(self, encoding='unicode'):
        return render_html(self.node, encoding=encoding)

    def attr(self, key, default=NULL):
        if default is NULL:
            if key in self.node.attrib:
                return self.node.get(key)
            else:
                raise DataNotFound(u'No such attribute: %s' % key)
        else:
            return self.node.get(key, default)

    def text(self, smart=False, normalize_space=True):
        elem = self.node
        if isinstance(elem, basestring):
            if normalize_space:
                return normalize_space_func(elem)
            else:
                return elem
        else:
            return get_node_text(elem, smart=smart,
                                 normalize_space=normalize_space)

    def number(self, default=NULL, ignore_spaces=False,
               smart=False, make_int=True):
        try:
            return find_number(self.text(smart=smart),
                               ignore_spaces=ignore_spaces,
                               make_int=make_int)
        except IndexError:
            if default is NULL:
                raise
            else:
                return default

    def rex(self, regexp, flags=0, byte=False):
        norm_regexp = rex_tools.normalize_regexp(regexp, flags)
        matches = list(norm_regexp.finditer(self.html()))
        return RexResultList(matches, source_rex=norm_regexp)


class RexResultList(object):
    __slots__ = ('items', 'source_rex')

    def __init__(self, items, source_rex):
        self.items = items
        self.source_rex = source_rex

    def one(self):
        return self.items[0]

    def text(self, default=NULL):
        try:
            return normalize_space(decode_entities(self.one().group(1)))
        except (AttributeError, IndexError):
            if default is NULL:
                raise
            else:
                return default

    def number(self):
        return int(self.text())


class TextSelector(LxmlNodeBaseSelector):
    __slots__ = ()

    def select(self, xpath=None):
        raise GrabMisuseError('TextSelector does not allow select method') 

    def html(self, encoding='unicode'):
        return self.node

    def attr(self, key, default=NULL):
        raise GrabMisuseError('TextSelector does not allow attr method') 


class XpathSelector(LxmlNodeBaseSelector):
    __slots__ = ()

    def process_query(self, query):
        from lxml.etree import XPath

        if not query in XPATH_CACHE:
            obj = XPath(query)
            XPATH_CACHE[query] = obj
        xpath_obj = XPATH_CACHE[query]

        result = xpath_obj(self.node)

        # If you query XPATH like //some/crap/@foo="bar" then xpath function
        # returns boolean value instead of list of something.
        # To work around this problem I just returns empty list.
        # This is not great solutions but it produces less confusing error.
        if isinstance(result, bool):
            result = []

        return result


class PyquerySelector(LxmlNodeBaseSelector):
    __slots__ = ()

    def pyquery_node(self):
        return PyQuery(self.node)

    def process_query(self, query):
        return self.pyquery_node().find(pyquery)


class KitSelector(BaseSelector):
    __slots__ = ()

    def process_query(self, query):
        return self.node.findAll(query)

    def html(self, encoding='unicode'):
        xml = self.node.toOuterXml()
        if encoding == 'unicode':
            return xml
        else:
            return xml.encode(encoding)

    def attr(self, key, default=NULL):
        if default is NULL:
            val = unicode(self.node.attribute(key, u'@NOTFOUND@'))
            if val == u'@NOTFOUND@':
                raise DataNotFound(u'No such attribute: %s' % key)
            else:
                return val
        else:
            return unicode(self.node.attribute(key, default))

    def text(self, smart=False, normalize_space=True):
        return unicode(self.node.toPlainText())


# ****************
# Deprecated Stuff
# ****************

class Selector(XpathSelector):
    __slots__ = ()

    def __init__(self, *args, **kwargs):
        super(Selector, self).__init__(*args, **kwargs)
        warn('Selector class is deprecated. '
             'Please use XpathSelector class instead.')
