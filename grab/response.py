"""
The Response class is the result of network request maden with Grab instance.
"""
import re
from copy import deepcopy

RE_XML_DECLARATION = re.compile(r'^<\?xml[^>]+\?>', re.I)
RE_DECLARATION_ENCODING = re.compile(r'encoding\s*=\s*["\']([^"\']+)["\']')
RE_META_CHARSET = re.compile(r'<meta[^>]+content\s*=\s*[^>]+charset=([-\w]+)', re.I)

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
        self.cookies = None
        self.charset = 'utf-8'

    def parse(self):
        """
        This method is called after Grab instance performes network request.
        """
        self.headers = {}
        for line in self.head.split('\n'):
            line = line.rstrip('\r')
            if line:
                if line.startswith('HTTP'):
                    self.status = line
                else:
                    try:
                        name, value = [x.strip() for x in line.split(':', 1)]
                        self.headers[name] = value
                    except ValueError, ex:
                        logging.error('Invalid header line: %s' % line, exc_info=ex)

        self.detect_charset()


    def detect_charset(self):
        charset = None

        # Try to extract charset from http-equiv meta tag
        if self.body:
            pos = self.body.lower().find('</head>')
            if pos > -1:
                html_head = self.body.lower()[:pos]
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
            self.charset = charset

    def unicode_body(self, ignore_errors=True):
        if ignore_errors:
            errors = 'ignore'
        else:
            errors = 'strict'
        ubody = self.body.decode(self.charset, errors)
        return RE_XML_DECLARATION.sub('', ubody)

    def copy(self):
        return deepcopy(self)
