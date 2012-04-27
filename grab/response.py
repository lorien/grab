"""
The Response class is the result of network request maden with Grab instance.
"""
import re
from copy import copy
import logging
import email
from StringIO import StringIO
#from cookielib import CookieJar
from urllib2 import Request
import os
import json
from urlparse import urlsplit, parse_qs
import tempfile
import webbrowser

from tools.files import hash_path

RE_XML_DECLARATION = re.compile(r'^[\r\n\t]*<\?xml[^>]+\?>', re.I)
RE_DECLARATION_ENCODING = re.compile(r'encoding\s*=\s*["\']([^"\']+)["\']')
RE_META_CHARSET = re.compile(r'<meta[^>]+content\s*=\s*[^>]+charset=([-\w]+)',
                             re.I)

class Response(object):
    """
    HTTP Response.
    """

    def __init__(self):
        self.status = None
        self.code = None
        self.head = None
        self.body = None
        self.headers =None
        self.time = None
        self.url = None
        self.cookies = {}
        #self.cookiejar = None
        self.charset = 'utf-8'
        self._unicode_body = None

    def parse(self, charset=None):
        """
        Parse headers and cookies.

        This method is called after Grab instance performes network request.
        """

        # Extract only valid lines which contain ":" character
        valid_lines = []
        for line in self.head.split('\n'):
            line = line.rstrip('\r')
            if line:
                # Each HTTP line meand the start of new response
                # self.head could contains info about multiple responses
                # For example, then 301/302 redirect was processed automatically
                # Maybe it is a bug and should be fixed
                # Anyway, we handle this issue here and save headers
                # only from last response
                if line.startswith('HTTP'):
                    self.status = line
                    valid_lines = []
                else:
                    if ':' in line:
                        valid_lines.append(line)

        self.headers = email.message_from_string('\n'.join(valid_lines))
        #self.cookiejar = CookieJar()
        #self.cookiejar._extract_cookies(self, Request(self.url))
        #for cookie in self.cookiejar:
            #self.cookies[cookie.name] = cookie.value

        if charset is None:
            self.detect_charset()
        else:
            self.charset = charset

        self._unicode_body = None

    def info(self):
        """
        This method need for using Response instance in
        ``Cookiejar.extract_cookies`` method.
        """

        return self.headers


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

        # Try to extract charset from http-equiv meta tag
        if self.body:
            chunk = self.body[:4096]
            try:
                charset = RE_META_CHARSET.search(chunk).group(1)
            except AttributeError:
                pass

        # TODO: <meta charset="utf-8" />

        # Try to process XML declaration
        if not charset:
            if self.body:
                if self.body.startswith('<?xml'):
                    match = RE_XML_DECLARATION.search(self.body)
                    if match:
                        enc_match = RE_DECLARATION_ENCODING.search(match.group(0))
                        if enc_match:
                            charset = enc_match.group(1)


        if not charset:
            if 'Content-Type' in self.headers:
                pos = self.headers['Content-Type'].find('charset=')
                if pos > -1:
                    charset = self.headers['Content-Type'][(pos + 8):]

        if charset:
            # Check that python know such charset
            try:
                u'x'.encode(charset)
            except LookupError:
                logging.error('Unknown charset found: %s' % charset)
                self.charset = 'utf-8'
            else:
                self.charset = charset

    def unicode_body(self, ignore_errors=True, strip_xml_declaration=False):
        """
        Return response body as unicode string.
        """

        if not self._unicode_body:
            if ignore_errors:
                errors = 'ignore'
            else:
                errors = 'strict'
            ubody = self.body.decode(self.charset, errors)
            if strip_xml_declaration:
                ubody = RE_XML_DECLARATION.sub('', ubody)
            self._unicode_body = ubody
        return self._unicode_body

    def copy(self):
        """
        Clone the Response object.
        """

        obj = Response()

        copy_keys = ('status', 'code', 'head', 'body', 'time',
                     'url', 'charset', '_unicode_body')
        for key in copy_keys:
            setattr(obj, key, getattr(self, key))

        obj.headers = copy(self.headers)
        obj.cookies = copy(self.cookies)
        #obj.cookiejar = copy(self.cookiejar)

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
            out.write(self.body)

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

        rel_path = hash_path(location, ext=ext)
        path = os.path.join(basedir, rel_path)
        if not os.path.exists(path):
            path_dir, path_fname = os.path.split(path)
            try:
                os.makedirs(path_dir)
            except OSError:
                pass
            with open(path, 'wb') as out:
                out.write(self.body)
        return rel_path

    @property
    def json(self):
        """
        Return response body deserialized into JSON object.
        """

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
