import pycurl
from StringIO import StringIO
import logging
import os
import urllib
import re
import random

from html import make_unicode, find_refresh_url, decode_entities
import user_agent

__all__ = ['Grab', 'request']

# We should ignore SIGPIPE when using pycurl.NOSIGNAL - see
# the libcurl tutorial for more info.
try:
    import signal
    from signal import SIGPIPE, SIG_IGN
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_IGN)
    # Ignore error in python 2.5
    except ValueError:
        pass
except ImportError:
    pass


DEFAULT_CONFIG = dict(
    timeout = 15,
    connect_timeout = 5,
    proxy = None,
    proxy_type = None,
    proxy_userpwd = None,
    proxy_file = None,
    proxy_random = True,
    proxy_list = False,
    post = None,
    payload = None,
    method = None,
    headers = {
        'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
        'Accept-Language': 'en-us;q=0.7,en,ru;q=0.3',
        'Accept-Charset': 'utf-8,windows-1251;q=0.7,*;q=0.7',
        'Keep-Alive': '300',
    },
    user_agent = random.choice(user_agent.variants),
    reuse_cookies = True,
    reuse_referer = True,
    cookies = {},
    referer = None,
    unicode_body = True,
    guess_encodings = ['windows-1251', 'koi8-r', 'utf-8'],
    decode_entities = False,
    log_file = None,
    follow_refresh = False,
    log_dir = False,
    nohead = False,
    nobody = False
)


def request(url, **kwargs):
    """
    Shortcut for single request.
    """

    grab = Grab()
    grab.setup(url=url, **kwargs)
    return grab.request()


class Grab(object):
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.curl = pycurl.Curl()
        self.counter = 0


    def setup(self, **kwargs):
        if 'headers' in kwargs:
            self.config['headers'].update(kwargs['headers'])
        self.config.update(kwargs)


    def head_processor(self, data):
        if self.config['nohead']:
            return 0
        self.response_head.append(data)
        return len(data)


    def body_processor(self, data):
        if self.config['nobody']:
            return 0
        self.response_body.append(data)
        return len(data)


    def process_config(self):
        """
        Setup curl instance with the config.
        """

        self.curl.setopt(pycurl.URL, str(self.config['url']))
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        self.curl.setopt(pycurl.MAXREDIRS, 5)
        self.curl.setopt(pycurl.CONNECTTIMEOUT, self.config['connect_timeout'])
        self.curl.setopt(pycurl.TIMEOUT, self.config['timeout'])
        self.curl.setopt(pycurl.NOSIGNAL, 1)
        self.curl.setopt(pycurl.WRITEFUNCTION, self.body_processor)
        self.curl.setopt(pycurl.HEADERFUNCTION, self.head_processor)
        self.curl.setopt(pycurl.USERAGENT, self.config['user_agent'])

        # Ignore SSL errors
        self.curl.setopt(pycurl.SSL_VERIFYPEER, 0)
        self.curl.setopt(pycurl.SSL_VERIFYHOST, 0)

        method = (self.config['method'] or '').upper()

        if not method:
            if self.config['payload'] or self.config['post']:
                method = 'POST'
            else:
                method = 'GET'

        if method == 'POST':
            self.curl.setopt(pycurl.POST, 1)
            if self.config['payload']:
                self.curl.setopt(pycurl.POSTFIELDS, self.config['payload'])
            elif self.config['post']:
                post_data = urllib.urlencode(self.config['post'])
                self.curl.setopt(pycurl.POSTFIELDS, post_data)
        elif method == 'PUT':
            self.curl.setopt(pycurl.PUT, 1)
            self.curl.setopt(pycurl.READFUNCTION, StringIO.StringIO(self.config['payload']).read) 
        elif method == 'DELETE':
            self.curl.setopt(pycurl.CUSTOMREQUEST, 'delete')
        else:
            # Assume the GET method
            self.curl.setopt(pycurl.HTTPGET, 1)
        
        logging.debug('[%02d] %s %s' % (self.counter, method, self.config['url']))

        if self.config['headers']:
            headers = [str('%s: %s' % x) for x in self.config['headers'].iteritems()]
            self.curl.setopt(pycurl.HTTPHEADER, headers)


        # CURLOPT_COOKIELIST
        # Pass a char * to a cookie string. Cookie can be either in Netscape / Mozilla format or just regular HTTP-style header (Set-Cookie: ...) format. If cURL cookie engine was not enabled it will enable its cookie engine. Passing a magic string "ALL" will erase all cookies known by cURL. (Added in 7.14.1) Passing the special string "SESS" will only erase all session cookies known by cURL. (Added in 7.15.4) Passing the special string "FLUSH" will write all cookies known by cURL to the file specified by CURLOPT_COOKIEJAR. (Added in 7.17.1)

        if self.config['reuse_cookies']:
            self.curl.setopt(pycurl.COOKIELIST, '')
        else:
            self.curl.setopt(pycurl.COOKIELIST, 'ALL')


        #CURLOPT_COOKIE
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


        """
        Proxy configuration
        You have three way to define proxy:
         1) Setup "proxy"
         2) Setup "proxy_file", which will fill the "proxy_list"
         3) Setup "proxy_list"
        For all three ways you can setup "proxy_type" and "proxy_userpwd"
        Also for 2nd and 3rd way you can setup "proxy_random" which is True by default
        """

        # Note that 'proxy_file' overwrite 'proxy' configuration
        if self.config['proxy_file']:
            self.load_proxy_file(self.config['proxy_file'])

        # Note that 'proxy_random' overwrite 'proxy' configuration
        if self.config['proxy_random'] and self.config['proxy_list']:
            self.config['proxy'] = random.choice(self.config['proxy_list'])

        if self.config['proxy']:
            # str is required to force unicode values
            self.curl.setopt(pycurl.PROXY, str(self.config['proxy'])) 

            # Pass a long with this option to set type of the proxy. Available options for this are CURLPROXY_HTTP, CURLPROXY_HTTP_1_0 (added in 7.19.4), CURLPROXY_SOCKS4 (added in 7.15.2), CURLPROXY_SOCKS5, CURLPROXY_SOCKS4A (added in 7.18.0) and CURLPROXY_SOCKS5_HOSTNAME (added in 7.18.0). The HTTP type is default. (Added in 7.10) 
            if self.config['proxy_userpwd']:
                self.curl.setopt(pycurl.PROXYUSERPWD, self.config['proxy_userpwd'])


        if self.config['proxy_type']:
            ptype = getattr(pycurl, 'PROXYTYPE_%s' % self.config['proxy_type'].upper())
            self.curl.setopt(pycurl.PROXYTYPE, ptype)

        if self.config['proxy']:
            if self.config['proxy_userpwd']:
                auth = ' with authorization'
            else:
                auth = ''
            logging.debug('Using proxy %s of type %s%s' % (
                self.config['proxy'], self.config['proxy_type'], auth))


    def load_proxy_file(self, path):
        if path != self.config['proxy_file'] or not self.config['proxy_list']:
            items = []
            for line in file(path):
                line = line.strip()
                if ':' in line:
                    items.append(line)
            self.config['proxy_list'] = items
            self.config['proxy'] = random.choice(self.config['proxy_list'])


    def parse_headers(self):
        for line in re.split('\r?\n', ''.join(self.response_head)):
            if line.startswith('HTTP'):
                self.response_status = line
            try:
                name, value = line.split(': ', 1)
                #if 'Set-Cookie' == name:
                    #match = re.search('^([^=]+)=([^;]+)*', value)
                    #if match:
                        #self.cookies[match.group(1)] = match.group(2)
                #else:
                self.headers[name] = value
            except ValueError:
                pass


    def parse_cookies(self):
        for line in self.curl.getinfo(pycurl.INFO_COOKIELIST):
            # Example of line:
            # www.google.com\tFALSE\t/accounts/\tFALSE\t0\tGoogleAccountsLocale_session\ten
            chunks = line.split('\t')
            key, value = chunks[-2:]
            self.cookies[key] = value


    def request(self):
        self.response_status = None
        self.response_code = None
        self.response_head = []
        self.response_body = []
        self.headers = {}
        self.cookies = {}
        self.counter += 1
        self._soup = None

        self.process_config()
        try:
            self.curl.perform()
        except pycurl.error, err:
            # CURLE_WRITE_ERROR
            # An error occurred when writing received data to a local file, or
            # an error was returned to libcurl from a write callback.
            # This is expected error and we should ignore it
            if 23 == err[0]:
                pass

        # It is very importent to delete old POST data after
        # request or that data will be used again in next request :-/
        self.config['post'] = None
        self.config['payload'] = None
        self.config['method'] = None

        self.response_code = self.curl.getinfo(pycurl.HTTP_CODE)
        #if 400 <= self.response_code:
            #raise IOError('Response code is %s: ' % self.response_code)
        self.response_head = ''.join(self.response_head)
        self.response_body = ''.join(self.response_body)
        self.original_response_body = self.response_body

        if self.config['unicode_body']:
            self.response_body = make_unicode(
                self.response_body, self.config['guess_encodings'])

            # Try to decode entities only if unicode_body option is set
            if self.config['decode_entities']:
                self.response_body = decode_entities(self.response_body)
        else:
            if self.config['decode_entities']:
                raise Exception('decode_entities option requires unicode_body option to be enabled')

        
        if self.config['log_file']:
            body = self.original_response_body
            file(self.config['log_file'], 'w').write(body)


        if self.config['log_dir']:
            fname = os.path.join(self.config['log_dir'], '%02d.html' % self.counter)
            body = self.original_response_body
            file(fname, 'w').write(self.response_head + body)

            fname = os.path.join(self.config['log_dir'], '%02d.orig' % self.counter)
            file(fname, 'w').write(body)
            

        self.parse_cookies()
        self.parse_headers()

        if self.config['reuse_referer']:
            self.config['referer'] = self.response_url()

        if self.config['follow_refresh']:
            url = find_refresh_url(self.original_response_body)
            if url:
                logging.debug('Following refresh url: %s' % url)
                # TODO check max redirect count
                self.setup(url=url)
                return self.request()


        response = {'body': self.response_body,
                    'headers': self.headers,
                    'time': self.response_time(),
                    'code': self.response_code,
                    'curl': self.curl,
                    'status': self.response_status,
                    'get_soup': lambda: self.soup,
                    }

        return response


    def response_time(self):
        return self.curl.getinfo(pycurl.TOTAL_TIME)


    def response_url(self):
        return self.curl.getinfo(pycurl.EFFECTIVE_URL)


    @property
    def soup(self):
        if not self._soup:
            from BeautifulSoup import BeautifulSoup
            #import html5lib
            #from html5lib import treebuilders
            if self.config['decode_entities']:
                raise Exception('You should not use BeautifulSoup with enabled decode_entities option')
            #parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("beautifulsoup"))
            #self._soup = parser.parse(self.original_response_body)
            self._soup = BeautifulSoup(self.original_response_body)
        return self._soup


    def input_value(self, name):
        elem = self.soup.find('input', attrs={'name': name})
        return elem['value'] if elem else None
