"""
The Response class is the result of network request maden with Grab instance.
"""
import re
from copy import copy
import logging
import email
from StringIO import StringIO
from cookielib import CookieJar
from urllib2 import Request

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
        self.cookiejar = None
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
                if line.startswith('HTTP'):
                    self.status = line
                else:
                    if ':' in line:
                        valid_lines.append(line)

        self.headers = email.message_from_string('\n'.join(valid_lines))
        #self.cookiejar = CookieJar()
        #self.cookiejar.extract_cookies(self, Request(self.url))
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
            body_lower = self.body.lower()
            pos = body_lower.find('</head>')
            if pos > -1:
                html_head = body_lower[:pos]
                if html_head.find('http-equiv') > -1:
                    try:
                        charset = RE_META_CHARSET.search(html_head).group(1)
                    except AttributeError:
                        pass

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

    def unicode_body(self, ignore_errors=True):
        """
        Return response body as unicode string.
        """

        if not self._unicode_body:
            if ignore_errors:
                errors = 'ignore'
            else:
                errors = 'strict'
            ubody = self.body.decode(self.charset, errors)
            self._unicode_body = RE_XML_DECLARATION.sub('', ubody)
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
        obj.cookiejar = copy(self.cookiejar)

        return obj

    def save(self, path):
        """
        Save response body to file.
        """

        with open(path, 'wb') as out:
            out.write(self.body)
