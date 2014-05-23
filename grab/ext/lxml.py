# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
from __future__ import absolute_import
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin
import re
import time
import logging
import traceback

from ..error import DataNotFound, GrabMisuseError
from ..tools.text import normalize_space as normalize_space_func, find_number
from ..tools.lxml_tools import get_node_text
from ..util.misc import deprecated

from grab.util.py3k_support import *

logger = logging.getLogger('grab.ext.lxml')
NULL = object()

#rex_script = re.compile(r'<script[^>]*>.+?</script>', re.S)
#rex_style = re.compile(r'<style[^>]*>.+?<?style>', re.S)
#rex_comment = re.compile(r'<!--(?:.(?!-->))-->', re.S)

#def simplify_html(html, targets=['script', 'style', 'comment']):
    #if 'script' in targets:
        #html = rex_script.sub(' ', html)
    #if 'style' in targets:
        #html = rex_style.sub(' ', html)
    #if 'comment' in targets:
        #html = rex_comment.sub(' ', html)
    #return html

class LXMLExtension(object):
    __slots__ = ()
    # SLOTS: _lxml_tree, _strict_lxml_tree

    @property
    @deprecated(use_instead='grab.doc.tree')
    def tree(self):
        return self.doc.tree

    @deprecated(use_instead='grab.doc.build_html_tree')
    def build_html_tree(self):
        return self.doc.build_html_tree()

    @property
    @deprecated(use_instead='grab.doc.xml_tree')
    def xml_tree(self):
        return self.doc.xml_tree
    
    @deprecated(use_instead='grab.doc.build_xml_tree()')
    def build_xml_tree(self):
        return self.doc.build_xml_tree()

    @deprecated()
    def find_link(self, href_pattern, make_absolute=True):
        """
        Find link in response body which href value matches ``href_pattern``.

        Returns found url or None.
        """

        if make_absolute:
            self.tree.make_links_absolute(self.response.url)

        if isinstance(href_pattern, unicode):
            raise GrabMisuseError('find_link method accepts only '\
                                  'byte-string argument')
        for elem, attr, link, pos in self.tree.iterlinks():
            if elem.tag == 'a' and href_pattern in link:
                return link
        return None

    @deprecated()
    def find_link_rex(self, rex, make_absolute=True):
        """
        Find link matched the given regular expression in response body.

        Returns found url or None.
        """

        if make_absolute:
            self.tree.make_links_absolute(self.response.url)

        for elem, attr, link, pos in self.tree.iterlinks():
            if elem.tag == 'a':
                match = rex.search(link)
                if match:
                    # That does not work for string object
                    # link.match = match
                    return link
        return None

    @deprecated()
    def follow_link(self, anchor=None, href=None):
        """
        Find link and follow it.

        # TODO: refactor this shit
        """

        if anchor is None and href is None:
            raise Exception('You have to provide anchor or href argument')
        self.tree.make_links_absolute(self.config['url'])
        for item in self.tree.iterlinks():
            if item[0].tag == 'a':
                found = False
                text = item[0].text or ''
                url = item[2]
                # if object is regular expression
                if anchor:
                    if hasattr(anchor, 'finditer'):
                        if anchor.search(text):
                            found = True
                    else:
                        if text.find(anchor) > -1:
                            found = True
                if href:
                    if hasattr(href, 'finditer'):
                        if href.search(url):
                            found = True
                    else:
                        if url.startswith(href) > -1:
                            found = True
                if found:
                    url = urljoin(self.config['url'], item[2])
                    return self.request(url=item[2])
        raise DataNotFound('Cannot find link ANCHOR=%s, HREF=%s' % (anchor, href))

    @deprecated(use_instead='grab.doc.select()')
    def xpath(self, *args, **kwargs):
        return self.xpath_one(*args, **kwargs)

    @deprecated(use_instead='grab.doc.select().one()')
    def xpath_one(self, path, default=NULL, filter=None):
        """
        Get first element which matches the given xpath or raise DataNotFound.
        """

        try:
            return self.xpath_list(path, filter)[0]
        except IndexError:
            if default is not NULL:
                return default
            else:
                raise DataNotFound('Xpath not found: %s' % path)

    @deprecated(use_instead='grab.doc.select()')
    def xpath_list(self, path, filter=None):
        """
        Find all elements which match given xpath.
        """

        items = self.tree.xpath(path)
        if filter:
            return [x for x in items if filter(x)]
        else:
            return items 

    @deprecated(use_instead='grab.doc.select().text()')
    def xpath_text(self, path, default=NULL, filter=None, smart=False,
                   normalize_space=True):
        """
        Get normalized text of node which matches the given xpath.
        """

        try:
            elem = self.xpath_one(path, filter=filter)
        except IndexError:
            if default is NULL:
                raise
            else:
                return default
        else:
            if isinstance(elem, basestring):
                return normalize_space_func(elem)
            else:
                return get_node_text(elem, smart=smart, normalize_space=normalize_space)

    @deprecated(use_instead='grab.doc.select().number()')
    def xpath_number(self, path, default=NULL, filter=None, ignore_spaces=False,
                     smart=False, make_int=True):
        """
        Find number in normalized text of node which matches the given xpath.
        """

        try:
            text = self.xpath_text(path, filter=filter, smart=smart)
            return find_number(text, ignore_spaces=ignore_spaces, make_int=make_int)
        except IndexError:
            if default is NULL:
                raise
            else:
                return default

    @deprecated()
    def css(self, *args, **kwargs):
        return self.css_one(*args, **kwargs)

    @deprecated()
    def css_one(self, path, default=NULL):
        """
        Get first element which matches the given css path or raise DataNotFound.
        """

        try:
            return self.css_list(path)[0]
        except IndexError:
            if default is NULL:
                raise DataNotFound('CSS path not found: %s' % path)
            else:
                return default

    @deprecated()
    def css_list(self, path):
        """
        Find all elements which match given css path.
        """

        return self.tree.cssselect(path)

    @deprecated()
    def css_text(self, path, default=NULL, smart=False, normalize_space=True):
        """
        Get normalized text of node which matches the css path.
        """

        try:
            return get_node_text(self.css_one(path), smart=smart,
                                 normalize_space=normalize_space)
        except IndexError:
            if default is NULL:
                raise
            else:
                return default

    @deprecated()
    def css_number(self, path, default=NULL, ignore_spaces=False, smart=False,
                   make_int=True):
        """
        Find number in normalized text of node which matches the given css path.
        """

        try:
            text = self.css_text(path, smart=smart)
            return find_number(text, ignore_spaces=ignore_spaces, make_int=make_int)
        except IndexError:
            if default is NULL:
                raise
            else:
                return default

    @deprecated()
    def strip_tags(self, content, smart=False):
        """
        Strip tags from the HTML content.
        """
        from lxml.html import fromstring

        return get_node_text(fromstring(content), smart=smart)

    @deprecated()
    def assert_css(self, path):
        """
        If css path is not found then raise `DataNotFound` exception.
        """

        self.css_one(path)

    @deprecated()
    def assert_xpath(self, path):
        """
        If xpath path is not found then raise `DataNotFound` exception.
        """

        self.xpath_one(path)

    @deprecated()
    def css_exists(self, path):
        """
        Return True if at least one element with specified css path exists.
        """

        return len(self.css_list(path)) > 0

    @deprecated(use_instead='grab.doc.select().exists()')
    def xpath_exists(self, path):
        """
        Return True if at least one element with specified xpath path exists.
        """

        return len(self.xpath_list(path)) > 0
