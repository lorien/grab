"""
The Response class is the result of network request maden with Grab instance.
"""
import re
from copy import copy
import logging
import email
#from cookielib import CookieJar
try:
    from urllib2 import Request
except ImportError:
    from urllib.request import Request
import os
import json
try:
    from urlparse import urlsplit, parse_qs
except ImportError:
    from urllib.parse import urlsplit, parse_qs
import tempfile
import webbrowser
import codecs
from datetime import datetime

from grab.tools import encoding as encoding_tools

from .tools.files import hashed_path

from grab.util.py3k_support import *

logger = logging.getLogger('grab.response')

RE_XML_DECLARATION = re.compile(br'^[^<]{,100}<\?xml[^>]+\?>', re.I)
RE_DECLARATION_ENCODING = re.compile(br'encoding\s*=\s*["\']([^"\']+)["\']')
RE_META_CHARSET = re.compile(br'<meta[^>]+content\s*=\s*[^>]+charset=([-\w]+)',
                             re.I)

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


class Response(object):
    """
    HTTP Response.
    """

    __slots__ = ('status', 'code', 'head', '_body', '_runtime_body',
                 'body_path', 'headers', 'url', 'cookies',
                 'charset', '_unicode_body', '_unicode_runtime_body',
                 'bom', 'timestamp',
                 'name_lookup_time', 'connect_time', 'total_time',
                 'download_size', 'upload_size', 'download_speed',
                 )

    def __init__(self):
        self.status = None
        self.code = None
        self.head = None
        self._body = None
        self._runtime_body = None
        #self.runtime_body = None
        self.body_path = None
        self.headers =None
        self.url = None
        self.cookies = {}
        #self.cookiejar = None
        self.charset = 'utf-8'
        self._unicode_body = None
        self._unicode_runtime_body = None
        self.bom = None
        self.timestamp = datetime.now()
        self.name_lookup_time = 0
        self.connect_time = 0
        self.total_time = 0
        self.download_size = 0
        self.upload_size = 0
        self.download_speed = 0

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
            if isinstance(self.body, unicode):
                self.charset = 'utf-8'
            else:
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

        body_chunk = None
        if self.body_path:
            with open(self.body_path, 'rb') as inp:
                body_chunk = inp.read(4096)
        elif self._body:
            body_chunk = self._body[:4096]

        if body_chunk:
            # Try to extract charset from http-equiv meta tag
            try:
                charset = RE_META_CHARSET.search(body_chunk).group(1)
            except AttributeError:
                pass

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
                        enc_match = RE_DECLARATION_ENCODING.search(match.group(0))
                        if enc_match:
                            charset = enc_match.group(1)

        if not charset:
            if 'Content-Type' in self.headers:
                pos = self.headers['Content-Type'].find('charset=')
                if pos > -1:
                    charset = self.headers['Content-Type'][(pos + 8):]

        if charset:
            if not isinstance(charset, str):
                # Convert to unicode (py2.x) or string (py3.x)
                charset = charset.decode('utf-8')
            # Check that python knows such charset
            try:
                codecs.lookup(charset)
            except LookupError:
                logger.error('Unknown charset found: %s' % charset)
                self.charset = 'utf-8'
            else:
                self.charset = charset

    def process_unicode_body(self, body, bom, charset, ignore_errors, fix_special_entities):
        if isinstance(body, unicode):
            #if charset in ('utf-8', 'utf8'):
            #    return body.strip()
            #else:
            #    body = body.encode('utf-8')
            #
            body = body.encode('utf-8')
        if bom:
            body = body[len(self.bom):]
        if fix_special_entities:
            body = encoding_tools.fix_special_entities(body)
        if ignore_errors:
            errors = 'ignore'
        else:
            errors = 'strict'
        return body.decode(charset, errors).strip()

    def unicode_body(self, ignore_errors=True, fix_special_entities=True):
        """
        Return response body as unicode string.
        """

        self._check_body()
        if not self._unicode_body:
            self._unicode_body = self.process_unicode_body(
                self._body, self.bom, self.charset,
                ignore_errors, fix_special_entities)
        return self._unicode_body

    def unicode_runtime_body(self, ignore_errors=True, fix_special_entities=True):
        """
        Return response body as unicode string.
        """

        if not self._unicode_runtime_body:
            self._unicode_runtime_body = self.process_unicode_body(
                self.runtime_body, None, self.charset,
                ignore_errors, fix_special_entities)
        return self._unicode_runtime_body

    def copy(self):
        """
        Clone the Response object.
        """

        obj = Response()

        copy_keys = ('status', 'code', 'head', 'body', 'total_time',
                     'connect_time', 'name_lookup_time',
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
            if isinstance(self._body, unicode):
                out.write(self._body.encode('utf-8'))
            else:
                out.write(self._body)

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

        if isinstance(location, unicode):
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
                if isinstance(self._body, unicode):
                    out.write(self._body.encode('utf-8'))
                else:
                    out.write(self._body)
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

    def _check_body(self):
        if not self._body:
            if self.body_path:
                with open(self.body_path, 'rb') as inp:
                    self._body = inp.read()

    def _read_body(self):
        # py3 hack
        if PY3K:
            return self.unicode_body()

        self._check_body()
        return self._body

    def _write_body(self, body):
        self._body = body
        self._unicode_body = None

    body = property(_read_body, _write_body)

    def _read_runtime_body(self):
        if self._runtime_body is None:
            return self._body
        else:
            return self._runtime_body

    def _write_runtime_body(self, body):
        self._runtime_body = body
        self._unicode_runtime_body = None

    runtime_body = property(_read_runtime_body, _write_runtime_body)

    def body_as_bytes(self, encode=False):
        self._check_body()
        if encode:
            return self.body.encode(self.charset)
        return self._body

    @property
    def time(self):
        logger.error('Attribute Response.time is deprecated. Use Response.total_time instead.')
        return self.total_time
