"""
Selector module provides high usability interface to lxml tree

Example of usage::

    >>> from lxml.html import fromstring
    >>> from grab.selector import Selector
    >>> HTML = '<body><h1>test</h1><ul><li>one: 1</li><li>two: 2</li></ul><span id="foo">FOO</span>'
    >>> sel = Selector(fromstring(HTML))
    >>> sel.select('//li')
    <grab.selector.selector.SelectorList object at 0x1aeaa90>
    >>> sel.select('//li')[0].node
    <Element li at 0x1adad10>
    >>> sel.select('//li')[0].node.text
    'one: 1'
    >>> sel.select('//li')[0].html()
    '<li>one: 1</li>'
    >>> sel.select('//span')[0].attr('id')
    'foo'
    >>> sel.select('//span/@id')[0]
    <grab.selector.selector.Selector object at 0x1aeaa50>
    >>> sel.select('//span').one().html()
    '<span id="foo">FOO</span>'
    >>> sel.select('//li').one().html()
    '<li>one: 1</li>'
    >>> sel.select('//li').text()
    'one: 1'
    >>> sel.select('//li').number()
    1
    >>> sel.select('//li').exists()
    True
"""
from __future__ import absolute_import
import logging
import time
from lxml.etree import XPath
try:
    from pyquery import PyQuery
except ImportError:
    pass

from ..tools.lxml_tools import get_node_text, render_html
from ..tools.text import find_number, normalize_space as normalize_space_func
from ..error import GrabMisuseError, DataNotFound
from ..tools import rex as rex_tools
from ..tools.text import normalize_space
from ..tools.html import decode_entities
from ..base import GLOBAL_STATE

__all__ = ['Selector', 'TextSelector']
NULL = object()
DEBUG_LOGGING = False
XPATH_CACHE = {}
logger = logging.getLogger('grab.selector.selector')


class SelectorList(object):
    def __init__(self, items, query_type, query_exp):
        self.items = items
        self.query_type = query_type
        self.query_exp = query_exp

    def __getitem__(self, x):
        return self.items[x]

    def __len__(self):
        return self.count()

    def count(self):
        return len(self.items)

    def one(self, default=NULL):
        try:
            return self.items[0]
        except IndexError:
            if default is NULL:
                raise DataNotFound('Could not get first item for %s: %s' % (
                    self.query_type, self.query_exp))
            else:
                return default

    def node(self):
        return self.one().node

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
        for item in self.items:
            result_list.append(item.text())
        return result_list

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
        Return True if selctor list is not empty.
        """

        return len(self.items) > 0

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
        for item in self.items:
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
        return [x.node for x in self.items]

    def node(self):
        return self.one().node

    def select(self, xpath=None, pyquery=None):
        result_list = None
        for count, item in enumerate(self.items):
            item_result_list = item.select(xpath=xpath, pyquery=pyquery)
            if count == 0:
                result_list = item_result_list
            else:
                result_list.items.extend(item_result_list.items)
        if result_list is None:
            # TODO: refactor
            if xpath is not None:
                query_type = 'xpath'
                query_exp = xpath
            else:
                query_type = 'pyquery'
                query_exp = pyquery
            return SelectorList([], query_type=query_type, query_exp=query_exp)
        return result_list


class Selector(object):
    def __init__(self, node):
        self.node = node

    def pyquery_node(self):
        return PyQuery(self.node)

    def select(self, xpath=None, pyquery=None):
        start = time.time()
        
        if xpath is None and pyquery is None:
            raise Exception('Both xpath and pyquery option are None')

        if xpath is not None and pyquery is not None:
            raise Exception('Both xpath and pyquery option are not None')

        if xpath is not None:
            if not xpath in XPATH_CACHE:
                obj = XPath(xpath)
                XPATH_CACHE[xpath] = obj
            xpath_obj = XPATH_CACHE[xpath]

            val = self.wrap_list(xpath_obj(self.node), 'xpath', xpath)
            query_exp = xpath
        else:
            val = self.wrap_list(self.pyquery_node().find(pyquery), 'pyquery', pyquery)
            query_exp = pyquery

        total = time.time() - start
        if DEBUG_LOGGING:
            logger.debug(u'Performed query [%s], elements: %d, time: %.05f sec' % (query_exp, len(val), total))
        GLOBAL_STATE['selector_time'] += total

        return val

    def wrap_list(self, items, query_type, query_exp):
        selectors = []
        for x in items:
            if isinstance(x, basestring):
                selectors.append(TextSelector(x))
            else:
                selectors.append(Selector(x))
        return SelectorList(selectors, query_type=query_type, query_exp=query_exp)

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
            return get_node_text(elem, smart=smart, normalize_space=normalize_space)

    def number(self, default=NULL, ignore_spaces=False,
               smart=False, make_int=True):
        try:
            return find_number(self.text(smart=smart), ignore_spaces=ignore_spaces,
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
    def __init__(self, items, source_rex):
        self.items = items
        self.source_rex = source_rex

    def one(self):
        return self.items[0]

    def text(self):
        return normalize_space(decode_entities(self.one().group(1)))

    def number(self):
        return int(self.text())


class TextSelector(Selector):
    def select(self, xpath=None):
        raise GrabMisuseError('TextSelector does not allow select method') 

    def html(self, encoding='unicode'):
        return self.node

    def attr(self, key, default=NULL):
        raise GrabMisuseError('TextSelector does not allow attr method') 
