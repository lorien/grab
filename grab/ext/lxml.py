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
from ..base import GLOBAL_STATE
from ..tools.text import normalize_space as normalize_space_func, find_number
from ..tools.lxml_tools import get_node_text
from ..response import RE_XML_DECLARATION
from ..tools.internal import deprecated

from grab.util.py3k_support import *

logger = logging.getLogger('grab.ext.lxml')

NULL = object()
NULL_BYTE = chr(0)

RE_UNICODE_XML_DECLARATION = re.compile(RE_XML_DECLARATION.pattern.decode('utf-8'), re.I)

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

    def extra_reset(self):
        self._lxml_tree = None
        self._strict_lxml_tree = None

    @property
    def tree(self):
        """
        Return DOM tree of the document built with HTML DOM builder.
        """

        if self.config['content_type'] == 'xml':
            return self.build_xml_tree()
        else:
            return self.build_html_tree()

    def build_html_tree(self):
        from lxml.html import fromstring
        from lxml.etree import ParserError

        if self._lxml_tree is None:
            body = self.response.unicode_runtime_body(
                fix_special_entities=self.config['fix_special_entities']
            ).strip()
            #if self.config['tidy']:
                #from tidylib import tidy_document
                #body, errors = tidy_document(body)
            if self.config['lowercased_tree']:
                body = body.lower()
            if self.config['strip_null_bytes']:
                body = body.replace(NULL_BYTE, '')
            # py3 hack
            if PY3K:
                body = RE_UNICODE_XML_DECLARATION.sub('', body)
            else:
                body = RE_XML_DECLARATION.sub('', body)
            if not body:
                # Generate minimal empty content
                # which will not break lxml parser
                body = '<html></html>'
            start = time.time()

            #body = simplify_html(body)
            try:
                self._lxml_tree = fromstring(body)
            except Exception as ex:
                if (isinstance(ex, ParserError)
                    and 'Document is empty' in str(ex)
                    and not '<html' in body):

                    # Fix for "just a string" body
                    body = '<html>%s</html>'.format(body)
                    self._lxml_tree = fromstring(body)

                elif (isinstance(ex, TypeError)
                      and "object of type 'NoneType' has no len" in str(ex)
                      and not '<html' in body):

                    # Fix for smth like "<frameset></frameset>"
                    body = '<html>%s</html>'.format(body)
                    self._lxml_tree = fromstring(body)
                else:
                    raise

            GLOBAL_STATE['dom_build_time'] += (time.time() - start)
        return self._lxml_tree

    @property
    def xml_tree(self):
        """
        Return DOM-tree of the document built with XML DOM builder.
        """
    
        logger.debug('This method is deprecated. Please use `tree` property '\
                     'and content_type="xml" option instead.')
        return self.build_xml_tree()

    def build_xml_tree(self):
        from lxml.etree import fromstring

        if self._strict_lxml_tree is None:
            # py3 hack
            if PY3K:
                body = self.response.body_as_bytes(encode=True)
            else:
                body = self.response.body
            self._strict_lxml_tree = fromstring(body)
        return self._strict_lxml_tree

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
        stack = traceback.extract_stack()
        stack_call = stack[-2]
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

    def css(self, *args, **kwargs):
        stack = traceback.extract_stack()
        stack_call = stack[-2]
        logger.debug('Method css is depricated. Please use css_one method. Location of problem: %s::%d' % (stack_call[0], stack_call[1]))
        return self.css_one(*args, **kwargs)

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

    def css_list(self, path):
        """
        Find all elements which match given css path.
        """

        return self.tree.cssselect(path)

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

    def strip_tags(self, content, smart=False):
        """
        Strip tags from the HTML content.
        """
        from lxml.html import fromstring

        return get_node_text(fromstring(content), smart=smart)

    def assert_css(self, path):
        """
        If css path is not found then raise `DataNotFound` exception.
        """

        self.css_one(path)

    def assert_xpath(self, path):
        """
        If xpath path is not found then raise `DataNotFound` exception.
        """

        self.xpath_one(path)

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

if __name__ == '__main__':
    main()
