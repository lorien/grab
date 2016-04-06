# Copyright: 2013, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: MIT
"""
The Document class is the result of network request made with Grab instance.
"""
from __future__ import absolute_import
import weakref
import re
from copy import copy
import email
import os
import json
import tempfile
import webbrowser
import codecs
from datetime import datetime
import time
from lxml.html import HTMLParser
from lxml.etree import XMLParser, parse, ParserError
from selection import XpathSelector
import six
from six.moves.urllib.parse import urlsplit, parse_qs, urljoin
import threading
from six import BytesIO, StringIO
from weblib.http import smart_urlencode
import weblib.encoding
from weblib.files import hashed_path
from weblib.structured import TreeInterface
from weblib.text import normalize_space
from weblib.html import decode_entities, find_refresh_url
from weblib.rex import normalize_regexp
import logging

from grab.cookie import CookieManager
from grab.error import GrabMisuseError, DataNotFound
from grab.const import NULL
from grab.util.warning import warn

NULL_BYTE = chr(0)
RE_XML_DECLARATION = re.compile(br'^[^<]{,100}<\?xml[^>]+\?>', re.I)
RE_DECLARATION_ENCODING = re.compile(br'encoding\s*=\s*["\']([^"\']+)["\']')
RE_META_CHARSET =\
    re.compile(br'<meta[^>]+content\s*=\s*[^>]+charset=([-\w]+)', re.I)
RE_META_CHARSET_HTML5 =\
    re.compile(br'<meta[^>]+charset\s*=\s*[\'"]?([-\w]+)', re.I)
RE_UNICODE_XML_DECLARATION =\
    re.compile(RE_XML_DECLARATION.pattern.decode('utf-8'), re.I)

# Bom processing logic was copied from
# https://github.com/scrapy/w3lib/blob/master/w3lib/encoding.py
_BOM_TABLE = [
    (codecs.BOM_UTF32_BE, 'utf-32-be'),
    (codecs.BOM_UTF32_LE, 'utf-32-le'),
    (codecs.BOM_UTF16_BE, 'utf-16-be'),
    (codecs.BOM_UTF16_LE, 'utf-16-le'),
    (codecs.BOM_UTF8, 'utf-8')
]
_FIRST_CHARS = set(char[0] for (char, name) in _BOM_TABLE)
THREAD_STORAGE = threading.local()
logger = logging.getLogger('grab.document')


def read_bom(data):
    """Read the byte order mark in the text, if present, and
    return the encoding represented by the BOM and the BOM.

    If no BOM can be detected, (None, None) is returned.
    """
    # common case is no BOM, so this is fast
    if data and data[0] in _FIRST_CHARS:
        for bom, encoding in _BOM_TABLE:
            if data.startswith(bom):
                return encoding, bom
    return None, None


class TextExtension(object):
    __slots__ = ()

    def text_search(self, anchor, byte=False):
        """
        Search the substring in response body.

        :param anchor: string to search
        :param byte: if False then `anchor` should be the
            unicode string, and search will be performed in
            `response.unicode_body()` else `anchor` should be the byte-string
            and search will be performed in `response.body`

        If substring is found return True else False.
        """

        if isinstance(anchor, six.text_type):
            if byte:
                raise GrabMisuseError('The anchor should be bytes string in '
                                      'byte mode')
            else:
                return anchor in self.unicode_body()

        if not isinstance(anchor, six.text_type):
            if byte:
                # if six.PY3:
                    # return anchor in self.body_as_bytes()
                return anchor in self.body
            else:
                raise GrabMisuseError('The anchor should be byte string in '
                                      'non-byte mode')

    def text_assert(self, anchor, byte=False):
        """
        If `anchor` is not found then raise `DataNotFound` exception.
        """

        if not self.text_search(anchor, byte=byte):
            raise DataNotFound(u'Substring not found: %s' % anchor)

    def text_assert_any(self, anchors, byte=False):
        """
        If no `anchors` were found then raise `DataNotFound` exception.
        """

        found = False
        for anchor in anchors:
            if self.text_search(anchor, byte=byte):
                found = True
                break
        if not found:
            raise DataNotFound(u'Substrings not found: %s'
                               % ', '.join(anchors))


class RegexpExtension(object):
    __slots__ = ()

    def rex_text(self, regexp, flags=0, byte=False, default=NULL):
        """
        Search regular expression in response body and return content of first
        matching group.

        :param byte: if False then search is performed in
        `response.unicode_body()` else the rex is searched in `response.body`.
        """

        try:
            match = self.rex_search(regexp, flags=flags, byte=byte)
        except DataNotFound:
            if default is NULL:
                raise DataNotFound('Regexp not found')
            else:
                return default
        else:
            return normalize_space(decode_entities(match.group(1)))

    def rex_search(self, regexp, flags=0, byte=False, default=NULL):
        """
        Search the regular expression in response body.

        :param byte: if False then search is performed in
        `response.unicode_body()` else the rex is searched in `response.body`.

        Note: if you use default non-byte mode than do not forget to build your
        regular expression with re.U flag.

        Return found match object or None

        """

        regexp = normalize_regexp(regexp, flags)
        match = None
        if byte:
            if not isinstance(regexp.pattern, six.text_type) or not six.PY3:
                # if six.PY3:
                    # body = self.body_as_bytes()
                # else:
                    # body = self.body
                match = regexp.search(self.body)
        else:
            if isinstance(regexp.pattern, six.text_type) or not six.PY3:
                ubody = self.unicode_body()
                match = regexp.search(ubody)
        if match:
            return match
        else:
            if default is NULL:
                raise DataNotFound('Could not find regexp: %s' % regexp)
            else:
                return default

    def rex_assert(self, rex, byte=False):
        """
        If `rex` expression is not found then raise `DataNotFound` exception.
        """

        self.rex_search(rex, byte=byte)


class PyqueryExtension(object):
    __slots__ = ()

    @property
    def pyquery(self):
        """
        Returns pyquery handler.
        """

        if not self._pyquery:
            from pyquery import PyQuery

            self._pyquery = PyQuery(self.body)
        return self._pyquery


class BodyExtension(object):
    __slots__ = ()

    def get_body_chunk(self):
        body_chunk = None
        if self.body_path:
            with open(self.body_path, 'rb') as inp:
                body_chunk = inp.read(4096)
        elif self._bytes_body:
            body_chunk = self._bytes_body[:4096]
        return body_chunk

    def convert_body_to_unicode(self, body, bom, charset,
                                ignore_errors, fix_special_entities):
        # How could it be unicode???
        # if isinstance(body, unicode):
            # body = body.encode('utf-8')
        if bom:
            body = body[len(self.bom):]
        if fix_special_entities:
            body = weblib.encoding.fix_special_entities(body)
        if ignore_errors:
            errors = 'ignore'
        else:
            errors = 'strict'
        return body.decode(charset, errors).strip()

    def read_body_from_file(self):
        with open(self.body_path, 'rb') as inp:
            return inp.read()

    def unicode_body(self, ignore_errors=True, fix_special_entities=True):
        """
        Return response body as unicode string.
        """

        if not self._unicode_body:
            self._unicode_body = self.convert_body_to_unicode(
                body=self.body,
                bom=self.bom,
                charset=self.charset,
                ignore_errors=ignore_errors,
                fix_special_entities=fix_special_entities,
            )
        return self._unicode_body

    def _read_body(self):
        if self.body_path:
            return self.read_body_from_file()
        else:
            return self._bytes_body

    def _write_body(self, body):
        if isinstance(body, six.text_type):
            raise GrabMisuseError('Document.body could be only byte string.')
        elif self.body_path:
            with open(self.body_path, 'wb') as out:
                out.write(body)
            self._bytes_body = None
        else:
            self._bytes_body = body
        self._unicode_body = None

    body = property(_read_body, _write_body)


class DomTreeExtension(object):
    __slots__ = ()

    @property
    def tree(self):
        """
        Return DOM tree of the document built with HTML DOM builder.
        """

        if self.grab.config['content_type'] == 'xml':
            return self.build_xml_tree()
        else:
            return self.build_html_tree()

    def _build_dom(self, content, mode):
        assert mode in ('html', 'xml')
        if mode == 'html':
            if not hasattr(THREAD_STORAGE, 'html_parser'):
                THREAD_STORAGE.html_parser = HTMLParser()
            dom = parse(StringIO(content),
                        parser=THREAD_STORAGE.html_parser)
            return dom.getroot()
        else:
            if not hasattr(THREAD_STORAGE, 'xml_parser'):
                THREAD_STORAGE.xml_parser = XMLParser()
            dom = parse(BytesIO(content),
                        parser=THREAD_STORAGE.xml_parser)
            return dom.getroot()


    def build_html_tree(self):
        from grab.base import GLOBAL_STATE

        if self._lxml_tree is None:
            fix_setting = self.grab.config['fix_special_entities']
            body = self.unicode_body(fix_special_entities=fix_setting).strip()
            if self.grab.config['lowercased_tree']:
                body = body.lower()
            if self.grab.config['strip_null_bytes']:
                body = body.replace(NULL_BYTE, '')
            # py3 hack
            if six.PY3:
                body = RE_UNICODE_XML_DECLARATION.sub('', body)
            else:
                body = RE_XML_DECLARATION.sub('', body)
            if not body:
                # Generate minimal empty content
                # which will not break lxml parser
                body = '<html></html>'
            start = time.time()

            try:
                self._lxml_tree = self._build_dom(body, 'html')
            except Exception as ex:
                if (isinstance(ex, ParserError)
                        and 'Document is empty' in str(ex)
                        and '<html' not in body):
                    # Fix for "just a string" body
                    body = '<html>%s</html>'.format(body)
                    self._lxml_tree = self._build_dom(body, 'html')

                elif (isinstance(ex, TypeError)
                      and "object of type 'NoneType' has no len" in str(ex)
                      and '<html' not in body):

                    # Fix for smth like "<frameset></frameset>"
                    body = '<html>%s</html>'.format(body)
                    self._lxml_tree = self._build_dom(body, 'html')
                else:
                    raise

            GLOBAL_STATE['dom_build_time'] += (time.time() - start)
        return self._lxml_tree

    @property
    def xml_tree(self):
        """
        Return DOM-tree of the document built with XML DOM builder.
        """
        warn('Attribute `grab.xml_tree` is deprecated. '
             'Use `Grab.doc.tree` attribute '
             'AND content_type="xml" option instead.')
        return self.build_xml_tree()

    def build_xml_tree(self):
        if self._strict_lxml_tree is None:
            self._strict_lxml_tree = self._build_dom(self.body, 'xml')
        return self._strict_lxml_tree


class FormExtension(object):
    __slots__ = ()

    def choose_form(self, number=None, id=None, name=None, xpath=None):
        """
        Set the default form.

        :param number: number of form (starting from zero)
        :param id: value of "id" attribute
        :param name: value of "name" attribute
        :param xpath: XPath query
        :raises: :class:`DataNotFound` if form not found
        :raises: :class:`GrabMisuseError`
            if method is called without parameters

        Selected form will be available via `form` attribute of `Grab`
        instance. All form methods will work with default form.

        Examples::

            # Select second form
            g.choose_form(1)

            # Select by id
            g.choose_form(id="register")

            # Select by name
            g.choose_form(name="signup")

            # Select by xpath
            g.choose_form(xpath='//form[contains(@action, "/submit")]')
        """

        if id is not None:
            try:
                self._lxml_form = self.select('//form[@id="%s"]' % id).node()
            except IndexError:
                raise DataNotFound("There is no form with id: %s" % id)
        elif name is not None:
            try:
                self._lxml_form = self.select(
                    '//form[@name="%s"]' % name).node()
            except IndexError:
                raise DataNotFound('There is no form with name: %s' % name)
        elif number is not None:
            try:
                self._lxml_form = self.tree.forms[number]
            except IndexError:
                raise DataNotFound('There is no form with number: %s' % number)
        elif xpath is not None:
            try:
                self._lxml_form = self.select(xpath).node()
            except IndexError:
                raise DataNotFound(
                    'Could not find form with xpath: %s' % xpath)
        else:
            raise GrabMisuseError('choose_form methods requires one of '
                                  '[number, id, name, xpath] arguments')

    @property
    def form(self):
        """
        This attribute points to default form.

        If form was not selected manually then select the form
        which has the biggest number of input elements.

        The form value is just an `lxml.html` form element.

        Example::

            g.go('some URL')
            # Choose form automatically
            print g.form

            # And now choose form manually
            g.choose_form(1)
            print g.form
        """

        if self._lxml_form is None:
            forms = [(idx, len(list(x.fields)))
                     for idx, x in enumerate(self.tree.forms)]
            if len(forms):
                idx = sorted(forms, key=lambda x: x[1], reverse=True)[0][0]
                self.choose_form(idx)
            else:
                raise DataNotFound('Response does not contains any form')
        return self._lxml_form

    def set_input(self, name, value):
        """
        Set the value of form element by its `name` attribute.

        :param name: name of element
        :param value: value which should be set to element

        To check/uncheck the checkbox pass boolean value.

        Example::

            g.set_input('sex', 'male')

            # Check the checkbox
            g.set_input('accept', True)
        """

        if self._lxml_form is None:
            self.choose_form_by_element('.//*[@name="%s"]' % name)
        elem = self.form.inputs[name]

        processed = False
        if getattr(elem, 'type', None) == 'checkbox':
            if isinstance(value, bool):
                elem.checked = value
                processed = True

        if not processed:
            # We need to remember original values of file fields
            # Because lxml will convert UploadContent/UploadFile object to
            # string
            if getattr(elem, 'type', '').lower() == 'file':
                self._file_fields[name] = value
                elem.value = ''
            else:
                elem.value = value

    def set_input_by_id(self, _id, value):
        """
        Set the value of form element by its `id` attribute.

        :param _id: id of element
        :param value: value which should be set to element
        """

        xpath = './/*[@id="%s"]' % _id
        if self._lxml_form is None:
            self.choose_form_by_element(xpath)
        sel = XpathSelector(self.form)
        elem = sel.select(xpath).node()
        return self.set_input(elem.get('name'), value)

    def set_input_by_number(self, number, value):
        """
        Set the value of form element by its number in the form

        :param number: number of element
        :param value: value which should be set to element
        """

        sel = XpathSelector(self.form)
        elem = sel.select('.//input[@type="text"]')[number].node()
        return self.set_input(elem.get('name'), value)

    def set_input_by_xpath(self, xpath, value):
        """
        Set the value of form element by xpath

        :param xpath: xpath path
        :param value: value which should be set to element
        """

        elem = self.select(xpath).node()

        if self._lxml_form is None:
            # Explicitly set the default form
            # which contains found element
            parent = elem
            while True:
                parent = parent.getparent()
                if parent.tag == 'form':
                    self._lxml_form = parent
                    break

        return self.set_input(elem.get('name'), value)

    # TODO:
    # Remove set_input_by_id
    # Remove set_input_by_number
    # New method: set_input_by(id=None, number=None, xpath=None)

    def submit(self, submit_name=None, make_request=True,
               url=None, extra_post=None):
        """
        Submit default form.

        :param submit_name: name of button which should be "clicked" to
            submit form
        :param make_request: if `False` then grab instance will be
            configured with form post data but request will not be
            performed
        :param url: explicitly specify form action url
        :param extra_post: (dict or list of pairs) additional form data which
            will override data automatically extracted from the form.

        Following input elements are automatically processed:

        * input[type="hidden"] - default value
        * select: value of last option
        * radio - ???
        * checkbox - ???

        Multipart forms are correctly recognized by grab library.

        Example::

            # Assume that we going to some page with some form
            g.go('some url')
            # Fill some fields
            g.set_input('username', 'bob')
            g.set_input('pwd', '123')
            # Submit the form
            g.submit()

            # or we can just fill the form
            # and do manual submission
            g.set_input('foo', 'bar')
            g.submit(make_request=False)
            g.request()

            # for multipart forms we can specify files
            from grab import UploadFile
            g.set_input('img', UploadFile('/path/to/image.png'))
            g.submit()
        """

        # TODO: add .x and .y items
        # if submit element is image

        post = self.form_fields()

        # Build list of submit buttons which have a name
        submit_controls = {}
        for elem in self.form.inputs:
            if (elem.tag == 'input' and elem.type == 'submit' and
                    elem.get('name') is not None):
                submit_controls[elem.name] = elem

        # All this code need only for one reason:
        # to not send multiple submit keys in form data
        # in real life only this key is submitted whose button
        # was pressed
        if len(submit_controls):
            # If name of submit control is not given then
            # use the name of first submit control
            if submit_name is None or submit_name not in submit_controls:
                controls = sorted(submit_controls.values(),
                                  key=lambda x: x.name)
                submit_name = controls[0].name

            # Form data should contain only one submit control
            for name in submit_controls:
                if name != submit_name:
                    if name in post:
                        del post[name]

        if url:
            action_url = urljoin(self.url, url)
        else:
            action_url = urljoin(self.url, self.form.action)

        # Values from `extra_post` should override values in form
        # `extra_post` allows multiple value of one key

        # Process saved values of file fields
        if self.form.method == 'POST':
            if 'multipart' in self.form.get('enctype', ''):
                for key, obj in self._file_fields.items():
                    post[key] = obj

        post_items = list(post.items())
        del post

        if extra_post:
            if isinstance(extra_post, dict):
                extra_post_items = extra_post.items()
            else:
                extra_post_items = extra_post

            # Drop existing post items with such key
            keys_to_drop = set([x for x, y in extra_post_items])
            for key in keys_to_drop:
                post_items = [(x, y) for x, y in post_items if x != key]

            for key, value in extra_post_items:
                post_items.append((key, value))

        if self.form.method == 'POST':
            if 'multipart' in self.form.get('enctype', ''):
                self.grab.setup(multipart_post=post_items)
            else:
                self.grab.setup(post=post_items)
            self.grab.setup(url=action_url)

        else:
            url = action_url.split('?')[0] + '?' + smart_urlencode(post_items)
            self.grab.setup(url=url)

        if make_request:
            return self.grab.request()
        else:
            return None

    def form_fields(self):
        """
        Return fields of default form.

        Fill some fields with reasonable values.
        """

        fields = dict(self.form.fields)
        for elem in self.form.inputs:
            # Ignore elements without name
            if not elem.get('name'):
                continue

            # Do not submit disabled fields
            # http://www.w3.org/TR/html4/interact/forms.html#h-17.12
            if elem.get('disabled'):
                if elem.name in fields:
                    del fields[elem.name]

            elif elem.tag == 'select':
                if fields[elem.name] is None:
                    if len(elem.value_options):
                        fields[elem.name] = elem.value_options[0]

            elif getattr(elem, 'type', None) == 'radio':
                if fields[elem.name] is None:
                    fields[elem.name] = elem.get('value')

            elif getattr(elem, 'type', None) == 'checkbox':
                if not elem.checked:
                    if elem.name is not None:
                        if elem.name in fields:
                            del fields[elem.name]

        return fields

    def choose_form_by_element(self, xpath):
        elem = self.select(xpath).node()
        while elem is not None:
            if elem.tag == 'form':
                self._lxml_form = elem
                return
            else:
                elem = elem.getparent()
        self._lxml_form = None


class Document(TextExtension, RegexpExtension, PyqueryExtension,
               BodyExtension, DomTreeExtension, FormExtension):
    """
    Document (in most cases it is a network response
        i.e. result of network request)
    """

    __slots__ = ('status', 'code', 'head', '_bytes_body',
                 'body_path', 'headers', 'url', 'cookies',
                 'charset', '_unicode_body',
                 'bom', 'timestamp',
                 'name_lookup_time', 'connect_time', 'total_time',
                 'download_size', 'upload_size', 'download_speed',
                 'error_code', 'error_msg', 'grab', 'remote_ip',
                 '_lxml_tree', '_strict_lxml_tree', '_pyquery',
                 '_lxml_form', '_file_fields', 'from_cache',
                 )

    def __init__(self, grab=None):
        if grab is None:
            self.grab = None
        else:
            if isinstance(grab, weakref.ProxyType):
                self.grab = grab
            else:
                self.grab = weakref.proxy(grab)

        self.status = None
        self.code = None
        self.head = None
        self.headers = None
        self.url = None
        self.cookies = CookieManager()
        self.charset = 'utf-8'
        self.bom = None
        self.timestamp = datetime.utcnow()
        self.name_lookup_time = 0
        self.connect_time = 0
        self.total_time = 0
        self.download_size = 0
        self.upload_size = 0
        self.download_speed = 0
        self.error_code = None
        self.error_msg = None
        self.from_cache = False

        # Body
        self.body_path = None
        self._bytes_body = None
        self._unicode_body = None

        # DOM Tree
        self._lxml_tree = None
        self._strict_lxml_tree = None

        # Pyquery
        self._pyquery = None

        # Form
        self._lxml_form = None
        self._file_fields = {}

    def __call__(self, query):
        return self.select(query)

    def select(self, *args, **kwargs):
        return XpathSelector(self.tree).select(*args, **kwargs)

    def structure(self, *args, **kwargs):
        return TreeInterface(self.tree).structured_xpath(*args, **kwargs)

    def parse(self, charset=None, headers=None):
        """
        Parse headers.

        This method is called after Grab instance performes network request.
        """

        if headers:
            self.headers = headers
        else:
            # Parse headers only from last response
            # There could be multiple responses in `self.head`
            # in case of 301/302 redirect
            # Separate responses
            if self.head:
                responses = self.head.rsplit(b'\nHTTP/', 1)
                # Cut off the 'HTTP/*' line from the last response
                _, response = responses[-1].split(b'\n', 1)
                response = response.decode('ascii', 'ignore')
            else:
                response = ''
            self.headers = email.message_from_string(response)

        if charset is None:
            if isinstance(self.body, six.text_type):
                self.charset = 'utf-8'
            else:
                self.detect_charset()
        else:
            self.charset = charset.lower()

        self._unicode_body = None

    def detect_charset(self):
        """
        Detect charset of the response.

        Try following methods:
        * meta[name="Http-Equiv"]
        * XML declaration
        * HTTP Content-Type header

        Ignore unknown charsets.

        Use utf-8 as fallback charset.
        """

        charset = None

        body_chunk = self.get_body_chunk()

        if body_chunk:
            # Try to extract charset from http-equiv meta tag
            match_charset = RE_META_CHARSET.search(body_chunk)
            if match_charset:
                charset = match_charset.group(1)
            else:
                match_charset_html5 = RE_META_CHARSET_HTML5.search(body_chunk)
                if match_charset_html5:
                    charset = match_charset_html5.group(1)

            # TODO: <meta charset="utf-8" />
            bom_enc, bom = read_bom(body_chunk)
            if bom_enc:
                charset = bom_enc
                self.bom = bom

            # Try to process XML declaration
            if not charset:
                if body_chunk.startswith(b'<?xml'):
                    match = RE_XML_DECLARATION.search(body_chunk)
                    if match:
                        enc_match = RE_DECLARATION_ENCODING.search(
                            match.group(0))
                        if enc_match:
                            charset = enc_match.group(1)

        if not charset:
            if 'Content-Type' in self.headers:
                pos = self.headers['Content-Type'].find('charset=')
                if pos > -1:
                    charset = self.headers['Content-Type'][(pos + 8):]

        if charset:
            charset = charset.lower()
            if not isinstance(charset, str):
                # Convert to unicode (py2.x) or string (py3.x)
                charset = charset.decode('utf-8')
            # Check that python knows such charset
            try:
                codecs.lookup(charset)
            except LookupError:
                logger.error('Unknown charset found: %s.'
                             ' Using utf-8 istead.' % charset)
                self.charset = 'utf-8'
            else:
                self.charset = charset

    def copy(self, new_grab=None):
        """
        Clone the Response object.
        """

        if new_grab is not None:
            obj = self.__class__(self.grab)  # Response()
        else:
            obj = self.__class__(new_grab)

        copy_keys = ('status', 'code', 'head', 'body', 'total_time',
                     'connect_time', 'name_lookup_time',
                     'url', 'charset', '_unicode_body')
        for key in copy_keys:
            setattr(obj, key, getattr(self, key))

        obj.headers = copy(self.headers)
        # TODO: Maybe, deepcopy?
        obj.cookies = copy(self.cookies)

        return obj

    def save(self, path, create_dirs=False):
        """
        Save response body to file.
        """

        path_dir, path_fname = os.path.split(path)
        if not os.path.exists(path_dir):
            try:
                os.makedirs(path_dir)
            except OSError:
                pass

        with open(path, 'wb') as out:
            out.write(self._bytes_body)

    def save_hash(self, location, basedir, ext=None):
        """
        Save response body into file with special path
        builded from hash. That allows to lower number of files
        per directory.

        :param location: URL of file or something else. It is
            used to build the SHA1 hash.
        :param basedir: base directory to save the file. Note that
            file will not be saved directly to this directory but to
            some sub-directory of `basedir`
        :param ext: extension which should be appended to file name. The
            dot is inserted automatically between filename and extension.
        :returns: path to saved file relative to `basedir`

        Example::

            >>> url = 'http://yandex.ru/logo.png'
            >>> g.go(url)
            >>> g.response.save_hash(url, 'some_dir', ext='png')
            'e8/dc/f2918108788296df1facadc975d32b361a6a.png'
            # the file was saved to $PWD/some_dir/e8/dc/...

        TODO: replace `basedir` with two options: root and save_to. And
        returns save_to + path
        """

        if isinstance(location, six.text_type):
            location = location.encode('utf-8')
        rel_path = hashed_path(location, ext=ext)
        path = os.path.join(basedir, rel_path)
        if not os.path.exists(path):
            path_dir, path_fname = os.path.split(path)
            try:
                os.makedirs(path_dir)
            except OSError:
                pass
            with open(path, 'wb') as out:
                out.write(self._bytes_body)
        return rel_path

    @property
    def json(self):
        """
        Return response body deserialized into JSON object.
        """

        if six.PY3:
            return json.loads(self.body.decode(self.charset))
        else:
            return json.loads(self.body)

    def url_details(self):
        """
        Return result of urlsplit function applied to response url.
        """

        return urlsplit(self.url)

    def query_param(self, key):
        """
        Return value of parameter in query string.
        """

        return parse_qs(self.url_details().query)[key][0]

    def browse(self):
        """
        Save response in temporary file and open it in GUI browser.
        """

        fh, path = tempfile.mkstemp()
        self.save(path)
        webbrowser.open('file://' + path)

    @property
    def time(self):
        warn('Attribute `Document.time` is deprecated. '
             'Use `Document.total_time` instead.')
        return self.total_time

    def __getstate__(self):
        """
        Reset cached lxml objects which could not be pickled.
        """
        state = {}
        for cls in type(self).mro():
            cls_slots = getattr(cls, '__slots__', ())
            for slot in cls_slots:
                if slot != '__weakref__':
                    if hasattr(self, slot):
                        state[slot] = getattr(self, slot)
        state['_lxml_tree'] = None
        state['_strict_lxml_tree'] = None
        state['_lxml_form'] = None
        return state

    def __setstate__(self, state):
        for slot, value in state.items():
            setattr(self, slot, value)

    def get_meta_refresh_url(self):
        return find_refresh_url(self.unicode_body())
