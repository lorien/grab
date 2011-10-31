# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
from __future__ import absolute_import
from lxml.html import fromstring
from lxml.cssselect import CSSSelector
from urlparse import urljoin
import re

from ..base import DataNotFound, GrabMisuseError

REX_NUMBER = re.compile(r'\d+')
REX_SPACE = re.compile(r'\s', re.U)

NULL = object()

class Extension(object):
    def extra_reset(self):
        self._lxml_tree = None

    @property
    def tree(self):
        """
        Return lxml ElementTree tree of the document.
        """

        if self._lxml_tree is None:
            body = self.response.unicode_body().strip()
            if self.config['lowercased_tree']:
                body = body.lower()
            if not body:
                # Generate minimal empty content
                # which will not break lxml parser
                body = '<html></html>'
            self._lxml_tree = fromstring(body)
        return self._lxml_tree

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
                text = item[0].text or u''
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

    def get_node_text(self, node):
        return self.normalize_space(' '.join(node.xpath('./descendant-or-self::*[name() != "script" and name() != "style"]/text()[normalize-space()]')))

    def find_node_number(self, node, ignore_spaces=False):
        return self.find_number(self.get_node_text(node), ignore_spaces=ignore_spaces)

    def xpath(self, path, default=NULL, filter=None):
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

    def xpath_list(self, path, filter=None):
        """
        Find all elements which match given xpath.
        """

        items = self.tree.xpath(path)
        if filter:
            return [x for x in items if filter(x)]
        else:
            return items 

    def xpath_text(self, path, default=NULL, filter=None):
        """
        Get normalized text of node which matches the given xpath.
        """

        try:
            elem = self.xpath(path, filter=filter)
        except IndexError:
            if default is NULL:
                raise
            else:
                return default
        else:
            if isinstance(elem, basestring):
                return self.normalize_space(elem)
            else:
                return self.get_node_text(elem)

    def xpath_number(self, path, default=NULL, filter=None, ignore_spaces=False):
        """
        Find number in normalized text of node which matches the given xpath.
        """

        try:
            return self.find_number(self.xpath_text(path, filter=filter),
                                    ignore_spaces=ignore_spaces)
        except IndexError:
            if default is NULL:
                raise
            else:
                return default

    def css(self, path, default=NULL):
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

    def css_list(self, path):
        """
        Find all elements which match given css path.
        """

        return self.tree.cssselect(path)

    def css_text(self, path, default=NULL):
        """
        Get normalized text of node which matches the css path.
        """

        try:
            return self.get_node_text(self.css(path))
        except IndexError:
            if default is NULL:
                raise
            else:
                return default

    def css_number(self, path, default=NULL, ignore_spaces=False):
        """
        Find number in normalized text of node which matches the given css path.
        """

        try:
            return self.find_number(self.css_text(path), ignore_spaces=ignore_spaces)
        except IndexError:
            if default is NULL:
                raise
            else:
                return default

    def strip_tags(self, content):
        """
        Strip tags from the HTML content.
        """

        return self.get_node_text(fromstring(content))

    def assert_css(self, path):
        """
        If css path is not found then raise `DataNotFound` exception.
        """

        self.css(path)

    def assert_xpath(self, path):
        """
        If xpath path is not found then raise `DataNotFound` exception.
        """

        self.xpath(path)

    def css_exists(self, path):
        """
        Return True if at least one element with specified css path exists.
        """

        return len(self.css_list(path)) > 0

    def xpath_exists(self, path):
        """
        Return True if at least one element with specified xpath path exists.
        """

        return len(self.xpath_list(path)) > 0
