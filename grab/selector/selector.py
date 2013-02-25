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
from ..tools.lxml_tools import get_node_text, render_html
from ..tools.text import find_number, normalize_space as normalize_space_func
from ..error import GrabMisuseError, DataNotFound
from ..tools import rex as rex_tools
from ..tools.text import normalize_space
from ..tools.html import decode_entities

__all__ = ['Selector', 'TextSelector']
NULL = object()

class SelectorList(object):
    def __init__(self, items, source_xpath):
        self.items = items
        self.source_xpath = source_xpath

    def __getitem__(self, x):
        return self.items[x]

    def one(self, default=NULL):
        try:
            return self.items[0]
        except IndexError:
            if default is NULL:
                raise DataNotFound('Could not get first item for xpath: %s' % self.source_xpath)
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
            return sel.number(ignore_spaces=ignore_spaces, smart=smart, make_int=make_int)

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


class Selector(object):
    def __init__(self, node):
        self.node = node

    def select(self, xpath=None):
        return self.wrap_list(self.node.xpath(xpath), xpath)

    def wrap_list(self, items, xpath):
        selectors = []
        for x in items:
            if isinstance(x, basestring):
                selectors.append(TextSelector(x))
            else:
                selectors.append(Selector(x))
        return SelectorList(selectors, source_xpath=xpath)

    def html(self, encoding='unicode'):
        return render_html(self.node, encoding=encoding)

    def attr(self, key, default=NULL):
        if default is NULL:
            return self.node.get(key)
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
        return find_number(self.text(smart=smart), ignore_spaces=ignore_spaces, make_int=make_int)

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

class TextSelector(Selector):
    def select(self, xpath=None):
        raise GrabMisuseError('TextSelector does not allow select method') 

    def html(self, encoding='unicode'):
        return self.node

    def attr(self, key, default=NULL):
        raise GrabMisuseError('TextSelector does not allow attr method') 
