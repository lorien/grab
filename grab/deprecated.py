from __future__ import absolute_import
from weblib.etree import get_node_text
from weblib.text import find_number
from weblib.const import NULL
from weblib.error import DataNotFound
from weblib.encoding import make_unicode
import six

from grab.util.warning import warn, deprecated
from grab.error import GrabMisuseError
from grab import error


class DeprecatedThings(object):
    __slots__ = ()

    """
    This super-class contains all deprecated things that are
    still in Grab class for back-ward compatibility.
    """

    # Deprecated methods from grab.ext.text module
    # ********************************************

    @deprecated(use_instead='grab.doc.text_search')
    def search(self, anchor, byte=False):
        return self.doc.text_search(anchor, byte=byte)

    @deprecated(use_instead='grab.doc.text_assert')
    def assert_substring(self, anchor, byte=False):
        return self.doc.text_assert(anchor, byte=byte)

    @deprecated(use_instead='grab.doc.text_assert_any')
    def assert_substrings(self, anchors, byte=False):
        return self.doc.text_assert_any(anchors, byte=byte)

    # Deprecated methods from grab.ext.rex module
    # ********************************************

    @deprecated(use_instead='grab.doc.rex_text')
    def rex_text(self, regexp, flags=0, byte=False, default=NULL):
        return self.doc.rex_text(regexp, flags=flags,
                                 byte=byte, default=default)

    @deprecated(use_instead='grab.doc.rex_search')
    def rex(self, regexp, flags=0, byte=False, default=NULL):
        return self.doc.rex_search(regexp, flags=flags,
                                   byte=byte, default=default)

    @deprecated(use_instead='grab.doc.rex_assert')
    def assert_rex(self, regexp, byte=False):
        return self.doc.rex_assert(regexp, byte=byte)

    # Deprecated methods from grab.ext.lxml
    # *************************************

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

        if isinstance(href_pattern, six.text_type):
            raise GrabMisuseError('Method `find_link` accepts only '
                                  'byte-string argument')
        href_pattern = make_unicode(href_pattern)
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

    @deprecated(use_instead='grab.doc.select().node()')
    def xpath(self, path, default=NULL, filter=None):
        if filter is not None:
            raise GrabMisuseError('Argument `filter` is not supported anymore')
        return self.doc.select(path).node(default=default)

    @deprecated(use_instead='grab.doc.select().one()')
    def xpath_one(self, path, default=NULL, filter=None):
        if filter is not None:
            raise GrabMisuseError('Argument `filter` is not supported anymore')
        return self.doc.select(path).node(default=default)

    @deprecated(use_instead='grab.doc.select()')
    def xpath_list(self, path, filter=None):
        if filter is not None:
            raise GrabMisuseError('Argument `filter` is not supported anymore')
        return self.doc.select(path).node_list()

    @deprecated(use_instead='grab.doc.select().text()')
    def xpath_text(self, path, default=NULL, filter=None, smart=False,
                   normalize_space=True):
        if filter is not None:
            raise GrabMisuseError('Argument `filter` is not supported anymore')
        return self.doc.select(path).text(default=default, smart=smart,
                                          normalize_space=normalize_space)

    @deprecated(use_instead='grab.doc.select().number()')
    def xpath_number(self, path, default=NULL, filter=None,
                     ignore_spaces=False,
                     smart=False, make_int=True):

        if filter is not None:
            raise GrabMisuseError('Argument `filter` is not supported anymore')
        return self.doc.select(path).number(default=default, smart=smart,
                                            ignore_spaces=ignore_spaces,
                                            make_int=make_int)

    @deprecated(use_instead='grab.doc.select().exists()')
    def xpath_exists(self, path):
        return self.doc.select(path).exists()

    @deprecated()
    def css(self, *args, **kwargs):
        return self.css_one(*args, **kwargs)

    @deprecated()
    def css_one(self, path, default=NULL):
        """
        Get first element which matches the given css path
            or raise DataNotFound.
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
        Find number in normalized text of node which
            matches the given css path.
        """

        try:
            text = self.css_text(path, smart=smart)
            return find_number(text, ignore_spaces=ignore_spaces,
                               make_int=make_int)
        except IndexError:
            if default is NULL:
                raise
            else:
                return default

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

    @deprecated()
    def strip_tags(self, content, smart=False):
        """
        Strip tags from the HTML content.
        """
        from lxml.html import fromstring

        return get_node_text(fromstring(content), smart=smart)

    # Methods from deprecated grab.ext.pquery module
    # **********************************************

    @deprecated(use_instead='grab.doc.pyquery()')
    def pyquery(self, query):
        return self.doc.pyquery(query)

    # Response related things
    # ***********************

    # Backward compat.
    def _get_response(self):
        return self.doc

    def _set_response(self, val):
        self.doc = val

    response = property(_get_response, _set_response)

    @deprecated(use_instead='grab.setup_document')
    def fake_response(self, *args, **kwargs):
        return self.setup_document(*args, **kwargs)

    # Cookies
    # *******
    @deprecated(use_instead='grab.cookies.load_from_file')
    def load_cookies(self, path, file_required=True):
        self.cookies.load_from_file(path)

    @deprecated(use_instead='grab.cookies.save_to_file')
    def dump_cookies(self, path):
        self.cookies.save_to_file(path)

    @deprecated(use_instead='grab.proxylist.load_file OR '
                            'grab.proxylist.load_url')
    def load_proxylist(self, source, source_type, proxy_type='http',
                       auto_init=True, auto_change=True,
                       **kwargs):
        # self.proxylist = ProxyList(source, source_type,
        #                            proxy_type=proxy_type, **kwargs)
        if source_type == 'text_file':
            self.proxylist.load_file(source, proxy_type=proxy_type)
        elif source_type == 'url':
            self.proxylist.load_url(source, proxy_type=proxy_type)
        else:
            raise error.GrabMisuseError(
                'Unknown proxy source type: %s' % source_type)

        # self.proxylist.setup(auto_change=auto_change, auto_init=auto_init)
        self.setup(proxy_auto_change=auto_change)
        if not auto_change and auto_init:
            self.change_proxy()

    # Methods from deprecated grab.ext.form module
    # **********************************************

    @deprecated(use_instead='grab.doc.choose_form')
    def choose_form(self, number=None, id=None, name=None, xpath=None):
        return self.doc.choose_form(number=number, id=id,
                                    name=name, xpath=xpath)

    @property
    def form(self):
        warn('The `Grab.form` attribute is deprecated. '
             'Use `Grab.doc.form` instead.')
        return self.doc.form

    @deprecated(use_instead='grab.doc.set_input')
    def set_input(self, name, value):
        return self.doc.set_input(name, value)

    @deprecated(use_instead='grab.doc.set_input_by_id')
    def set_input_by_id(self, _id, value):
        return self.doc.set_input_by_id(_id, value)

    @deprecated(use_instead='grab.doc.set_input_by_number')
    def set_input_by_number(self, number, value):
        return self.doc.set_input_by_number(number, value)

    @deprecated(use_instead='grab.doc.set_input_by_xpath')
    def set_input_by_xpath(self, xpath, value):
        return self.doc.set_input_by_xpath(xpath, value)

    @deprecated(use_instead='grab.doc.submit')
    def submit(self, submit_name=None, make_request=True,
               url=None, extra_post=None):
        return self.doc.submit(submit_name=submit_name,
                               make_request=make_request,
                               url=url, extra_post=extra_post)

    @deprecated(use_instead='grab.doc.form_fields')
    def form_fields(self):
        return self.doc.form_fields()

    @deprecated(use_instead='grab.doc.choose_form_by_element')
    def choose_form_by_element(self, xpath):
        return self.doc.choose_form_by_element(xpath)
