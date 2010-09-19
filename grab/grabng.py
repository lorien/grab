# -*- coding: utf-8 -*-
import pycurl
#from StringIO import StringIO
import logging
#import os
#import urllib
import re
from random import randint, choice
#from copy import deepcopy, copy
#import threading
#from urlparse import urljoin
#import email

#from html import make_unicode, find_refresh_url
import user_agent

logger = logging.getLogger('grab')
__all__ = ['Grab']

DEFAULT_EXTENSIONS = ['grab.ext.lxml', 'grab.ext.lxml_form']

# @lorien: I do not understand these signals. Maybe you?

# We should ignore SIGPIPE when using pycurl.NOSIGNAL - see
# the libcurl tutorial for more info.

# http://curl.haxx.se/mail/curlpython-2005-06/0004.html
# http://curl.haxx.se/mail/lib-2010-03/0114.html

#CURLOPT_NOSIGNAL
#Pass a long. If it is 1, libcurl will not use any functions that install signal handlers or any functions that cause signals to be sent to the process. This option is mainly here to allow multi-threaded unix applications to still set/use all timeout options etc, without risking getting signals. (Added in 7.10)
#If this option is set and libcurl has been built with the standard name resolver, timeouts will not occur while the name resolve takes place. Consider building libcurl with c-ares support to enable asynchronous DNS lookups, which enables nice timeouts for name resolves without signals.

try:
    import signal
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
except ImportError:
    pass

class GrabError(pycurl.error):
    """
    Wrapper for ``pycurl.error``
    """

    pass

class DataNotFound(Exception):
    pass

def REX_INPUT(name):
    return re.compile(r'<input[^>]+name\s*=\s*["\']?%s["\' ][^>]*>' % re.escape(name), re.S)
REX_VALUE = re.compile(r'value\s*=\s*["\']?([^"\'> ]+)', re.S)

def clone_config(cfg):
    """
    Similar to copy.deepcopy but works faster.
    """

    res = {}
    for key, value in cfg.iteritems():
        if isinstance(value, (list, dict)):
            res[key] = copy(value)
        else:
            res[key] = copy(value)
    return res


def default_config():
    return dict(
        timeout = 15,
        connect_timeout = 10,
        proxy = None,
        proxy_type = None,
        proxy_userpwd = None,
        proxy_file = None,
        proxy_random = True,
        proxy_list = False,
        post = None,
        payload = None,
        method = None,
        headers = {},
        charset = 'utf-8',
        user_agent = choice(user_agent.variants),
        reuse_cookies = True,
        reuse_referer = True,
        cookies = {},
        referer = None,
        unicode_body = False,
        guess_encodings = ['windows-1251', 'koi8-r', 'utf-8'],
        log_file = None,
        log_dir = False,
        follow_refresh = False,
        nohead = False,
        nobody = False,
        debug = False,
    )

class Response(object):
    """
    HTTP Response.
    """

    keys = ['status', 'code', 'head', 'body', 'headers',
            'time', 'url']

    def __init__(self):
        for key in self.keys:
            setattr(self, key, None)

    def clone():
        obj = Response()
        for key in keys:
            setattr(obj, key, getattr(self, key))
        return obj

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
                        name, value = line.split(': ', 1)
                        self.headers[name] = value
                    except ValueError, ex:
                        logging.error('Invalid header line: %s' % line)

    @property
    def unicode_body(self):
        if not self._unicode_body:
            self._unicode_body = make_unicode(self.response_body, self.config['guess_encodings'])
        return self._unicode_body


class Grab(object):
    # Shortcut to grab.GrabError
    Error = GrabError

    # This counter will used in enumerating network queries.
    # Its values will be displayed in logging messages and also used
    # in names of dumps
    request_counter = -1

    # Attributes which should be processed when clone
    # of Grab instance is creating
    clonable_attributes = ['request_headers', 'cookies', 'request_counter']

    # Info about loaded extensions
    extensions = []

    def __init__(self, extensions=DEFAULT_EXTENSIONS, extra_extensions=None):
        if extra_extensions:
            extensions = extensions + extra_extensions
        for mod_path in extensions:
            # Can't win in the fight with relative imports...
            # Doing simple hack
            if mod_path.startswith('grab.'):
                mod_path = mod_path[5:]
            mod = __import__(mod_path, globals(), locals(), ['foo'])
            self.load_extension(mod.Extension)
        self.config = default_config()
        for ext in self.extensions:
            try:
                self.config.update(ext.extra_default_config())
            except AttributeError:
                pass
        self.default_headers = self.common_headers()
        self.curl = pycurl.Curl()
        self.reset()

    def load_extension(self, ext_class):
        for attr in ext_class.export_attributes:
            self.add_to_class(attr, ext_class.__dict__[attr])
        self.extensions.append(ext_class())

    @classmethod
    def add_to_class(cls, name, obj):
        setattr(cls, name, obj)

    def common_headers(self):
        """
        Build headers which sends typical browser.
        """

        return {
            'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.%d' % randint(2, 5),
            'Accept-Language': 'en-us;q=0.%d,en,ru;q=0.%d' % (randint(5, 9), randint(1, 4)),
            'Accept-Charset': 'utf-8,windows-1251;q=0.7,*;q=0.%d' % randint(5, 7),
            'Keep-Alive': '300',
        }

    def reset(self):
        """
        Reset all attributes which could be modified during previous request
        or which is not initialized yet if this is the new Grab instance.
        """

        self.response = Response()
        self.request_headers = None
        self.cookies = {}
        self.request_counter += 1
        self._soup = None
        self.response_head_chunks = []
        self.response_body_chunks = []

        for ext in self.extensions:
            try:
                ext.extra_reset(self)
            except AttributeError:
                pass

    def clone(self):
        """
        Create clone of Grab instance.

        Try to save its state: cookies, referer, response data
        """

        g = Grab()
        g.config = clone_config(self.config)
        g.setup(cookies=self.cookies)
        g.response = self.response.clone()
        for key in self.clonable_attributes:
            setattr(g, key, getattr(self, key))
        return g

    def setup(self, **kwargs):
        """
        Change configuration.
        """

        self.config.update(kwargs)

    def head_processor(self, chunk):
        """
        Process head of response.
        """

        if self.config['nohead']:
            return 0
        self.response_head_chunks.append(chunk)
        return len(chunk)

    def body_processor(self, chunk):
        """
        Process body of response.
        """

        if self.config['nobody']:
            return 0
        self.response_body_chunks.append(chunk)
        return len(chunk)

    def debug_processor(self, _type, text):
        """
        Parse request headers and save to ``self.request_headers``
        """

        if _type == pycurl.INFOTYPE_HEADER_OUT:
            text = '\n'.join(text.splitlines()[1:])
            self.request_headers = dict(email.message_from_string(text))

    def process_config(self):
        """
        Setup curl instance with values from ``self.config``.
        """

        url = self.config['url']
        if isinstance(url, unicode):
            url = url.encode('utf-8')
        self.curl.setopt(pycurl.URL, url)
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        self.curl.setopt(pycurl.MAXREDIRS, 5)
        self.curl.setopt(pycurl.CONNECTTIMEOUT, self.config['connect_timeout'])
        self.curl.setopt(pycurl.TIMEOUT, self.config['timeout'])
        self.curl.setopt(pycurl.NOSIGNAL, 1)
        self.curl.setopt(pycurl.WRITEFUNCTION, self.body_processor)
        self.curl.setopt(pycurl.HEADERFUNCTION, self.head_processor)
        self.curl.setopt(pycurl.USERAGENT, self.config['user_agent'])

        if self.config['debug']:
            self.curl.setopt(pycurl.VERBOSE, 1)
            self.curl.setopt(pycurl.DEBUGFUNCTION, self.debug_processor)

        # Ignore SSL errors
        self.curl.setopt(pycurl.SSL_VERIFYPEER, 0)
        self.curl.setopt(pycurl.SSL_VERIFYHOST, 0)

        method = self.config['method']
        if method:
            method = method.upper()
        else:
            if self.config['payload'] or self.config['post']:
                method = 'POST'
            else:
                method = 'GET'

        if method == 'POST':
            self.curl.setopt(pycurl.POST, 1)
            if self.config['payload']:
                self.curl.setopt(pycurl.POSTFIELDS, self.config['payload'])
            elif self.config['post']:
                post_data = self.urlencode(self.config['post'])
                self.curl.setopt(pycurl.POSTFIELDS, post_data)
        elif method == 'PUT':
            self.curl.setopt(pycurl.PUT, 1)
            self.curl.setopt(pycurl.READFUNCTION, StringIO(self.config['payload']).read) 
        elif method == 'DELETE':
            self.curl.setopt(pycurl.CUSTOMREQUEST, 'delete')
        else:
            self.curl.setopt(pycurl.HTTPGET, 1)
        
        headers = self.default_headers
        if self.config['headers']:
            headers.update(self.config['headers'])
        headers_tuples = [str('%s: %s' % x) for x\
                          in self.config['headers'].iteritems()]
        self.curl.setopt(pycurl.HTTPHEADER, headers_tuples)


        # CURLOPT_COOKIELIST
        # Pass a char * to a cookie string. Cookie can be either in Netscape / Mozilla format or just regular HTTP-style header (Set-Cookie: ...) format.
        # If cURL cookie engine was not enabled it will enable its cookie engine.
        # Passing a magic string "ALL" will erase all cookies known by cURL. (Added in 7.14.1)
        # Passing the special string "SESS" will only erase all session cookies known by cURL. (Added in 7.15.4)
        # Passing the special string "FLUSH" will write all cookies known by cURL to the file specified by CURLOPT_COOKIEJAR. (Added in 7.17.1)

        if self.config['reuse_cookies']:
            # Setting empty string will activate curl cookie engine
            self.curl.setopt(pycurl.COOKIELIST, '')
        else:
            self.curl.setopt(pycurl.COOKIELIST, 'ALL')


        # CURLOPT_COOKIE
        # Pass a pointer to a zero terminated string as parameter. It will be used to set a cookie in the http request. The format of the string should be NAME=CONTENTS, where NAME is the cookie name and CONTENTS is what the cookie should contain.
        # If you need to set multiple cookies, you need to set them all using a single option and thus you need to concatenate them all in one single string. Set multiple cookies in one string like this: "name1=content1; name2=content2;" etc.
        # Note that this option sets the cookie header explictly in the outgoing request(s). If multiple requests are done due to authentication, followed redirections or similar, they will all get this cookie passed on.
        # Using this option multiple times will only make the latest string override the previous ones. 

        if self.config['cookies']:
            chunks = []
            for key, value in self.config['cookies'].iteritems():
                key = urllib.quote_plus(key)
                value = urllib.quote_plus(value)
                chunks.append('%s=%s;' % (key, value))
            self.curl.setopt(pycurl.COOKIE, ''.join(chunks))

        if self.config['referer']:
            self.curl.setopt(pycurl.REFERER, str(self.config['referer']))

        if self.config['proxy']:
            self.curl.setopt(pycurl.PROXY, str(self.config['proxy'])) 

        if self.config['proxy_userpwd']:
            self.curl.setopt(pycurl.PROXYUSERPWD, self.config['proxy_userpwd'])

        # PROXYTYPE
        # Pass a long with this option to set type of the proxy. Available options for this are CURLPROXY_HTTP, CURLPROXY_HTTP_1_0 (added in 7.19.4), CURLPROXY_SOCKS4 (added in 7.15.2), CURLPROXY_SOCKS5, CURLPROXY_SOCKS4A (added in 7.18.0) and CURLPROXY_SOCKS5_HOSTNAME (added in 7.18.0). The HTTP type is default. (Added in 7.10) 

        if self.config['proxy_type']:
            ptype = getattr(pycurl, 'PROXYTYPE_%s' % self.config['proxy_type'].upper())
            self.curl.setopt(pycurl.PROXYTYPE, ptype)

        if self.config['proxy']:
            if self.config['proxy_userpwd']:
                auth = ' with authorization'
            else:
                auth = ''
            proxy_info = ' via %s proxy of type %s%s' % (
                self.config['proxy'], self.config['proxy_type'], auth)
        else:
            proxy_info = ''

        logger.debug('[%02d] %s %s%s' % (self.request_counter, method, self.config['url'], proxy_info))

    def extract_cookies(self):
        """
        Extract cookies.
        """

        # Example of line:
        # www.google.com\tFALSE\t/accounts/\tFALSE\t0\tGoogleAccountsLocale_session\ten
        cookies = {}
        for line in self.curl.getinfo(pycurl.INFO_COOKIELIST):
            chunks = line.split('\t')
            cookies[chunks[-2]] = chunks[-1]
        return cookies

    def go(self, url):
        """
        Go to ``url``

        Args:
            :url: could be absolute or relative. If relative then will be appended to the
                absolute URL of previous request.
        """

        if self.config.get('url'):
            url = urljoin(self.config['url'], url)
        return self.request(url=url)


    def request(self, **kwargs):
        # Reset the state setted by prevous request
        self.reset()
        if kwargs:
            self.setup(**kwargs)
        self.process_config()
        try:
            self.curl.perform()
        except pycurl.error, ex:
            # CURLE_WRITE_ERROR
            # An error occurred when writing received data to a local file, or
            # an error was returned to libcurl from a write callback.
            # This is expected error and we should ignore it
            if 23 == ex[0]:
                pass
            else:
                raise GrabError(ex[0], ex[1])

        # It's vital to delete old POST data after request is performed.
        # If POST data remains when next request will try to use them again!
        # This is not what typical user waits.
        self.config['post'] = None
        self.config['payload'] = None
        self.config['method'] = None

        self.prepare_response()

        # TODO: raise GrabWarning if self.config['http_warnings']
        #if 400 <= self.response_code:
            #raise IOError('Response code is %s: ' % self.response_code)

        if self.config['log_file']:
            open(self.config['log_file'], 'w').write(self.response.body)

        self.save_dumps()

        if self.config['reuse_referer']:
            self.config['referer'] = self.response.url

        # TODO: check max redirect count
        if self.config['follow_refresh']:
            url = find_refresh_url(self.response_body)
            if url:
                return self.request(url=url)

    def prepare_response(self):
        self.response.head = ''.join(self.response_head_chunks)
        self.response.body = ''.join(self.response_body_chunks)
        self.response.parse()
        self.response.cookies = self.extract_cookies()
        self.response.code = self.curl.getinfo(pycurl.HTTP_CODE)
        self.response.time = self.curl.getinfo(pycurl.TOTAL_TIME)
        self.response.url = self.curl.getinfo(pycurl.EFFECTIVE_URL)

    def save_dumps(self):
        if self.config['log_dir']:
            tname = threading.currentThread().getName().lower()
            if tname == 'mainthread':
                tname = ''
            else:
                tname = '-%s' % tname
            fname = os.path.join(self.config['log_dir'], '%02d%s.log' % (self.request_counter, tname))
            open(fname, 'w').write(self.response.head)

            fext = 'html'
            #dirs = self.response_url().split('//')[1].strip().split('/')
            #if len(dirs) > 1:
                #fext = dirs[-1].split('.')[-1]
                
            fname = os.path.join(self.config['log_dir'], '%02d%s.%s' % (self.request_counter, tname, fext))
            open(fname, 'w').write(self.response.body)

    def input_value(self, name):
        """
        Return the value of INPUT element.

        This method does not use DOM parses, just simple regular expressions.
        """

        try:
            elem = REX_INPUT(name).search(self.response_body).group(0)
        except AttributeError:
            return None
        else:
            try:
                return REX_VALUE.search(elem).group(1)
            except AttributeError:
                return None

    def repeat(self, anchor, action=None, limit=10, args=None):
        """
        Make requests until ``acnhor`` found in 
        response body or number of request exeeds the ``limit``
        """

        for x in xrange(limit):
            if args:
                self.setup(**args)
            if action:
                action()
            else:
                self.request()
            if isinstance(anchor, (list, tuple)):
                searches = anchor
            else:
                searches = [anchor]
            for search in searches:
                if search in self.response_body:
                    return
        else:
            message = 'Substring "%s" not found in response.' % anchor
            if isinstance(message, unicode):
                message = message.encode('utf-8')
            raise IOError(message)

    def urlencode(self, items):
        """
        Smart urlencode which know how to process unicode strings and None values.
        """

        if isinstance(items, dict):
            items = items.items()
        def process(item):
            key, value = item
            if isinstance(value, unicode):
                value = value.encode(self.config['charset'])
            elif value is None:
                value = ''
            return key, value
        return urllib.urlencode(map(process, items))

    def search(self, anchor):
        """
        Search for string or regular expression.
        """

        if hasattr(anchor, 'finditer'):
            return rex.search(self.response_body) or None
        else:
            if isinstance(anchor, unicode):
                anchor = anchor.encode(self.config['charset'])
            return anchor if self.response_body.find(anchor) > -1 else None

    def assert_pattern(self, anchor):
        """
        Search for string or regexp.
        
        If nothing found raise DataNotFound exception.
        """

        if not self.search(*args, **kwargs):
            raise DataNotFound(u'Could not found pattern: %s' % anchor)

    def reload(self):
        """
        Load current url again.
        """

        g.go('')
