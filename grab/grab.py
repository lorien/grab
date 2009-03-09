import pycurl
from StringIO import StringIO
import logging
import os
import urllib
import re

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
    post = None,
    payload = None,
    headers = None,
    method = None
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


    def setup(self, **kwargs):
        self.config.update(kwargs)


    def head_processor(self, data):
        self.response_head.append(data)
        return len(data)


    def body_processor(self, data):
        self.response_body.append(data)
        return len(data)


    def process_config(self):
        """
        Setup curl instance with the config.
        """

        logging.debug('URL: %s' % self.config['url'])
        self.curl.setopt(pycurl.URL, self.config['url'])
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        self.curl.setopt(pycurl.MAXREDIRS, 5)
        self.curl.setopt(pycurl.CONNECTTIMEOUT, self.config['connect_timeout'])
        self.curl.setopt(pycurl.TIMEOUT, self.config['timeout'])
        self.curl.setopt(pycurl.NOSIGNAL, 1)
        self.curl.setopt(pycurl.WRITEFUNCTION, self.body_processor)
        self.curl.setopt(pycurl.HEADERFUNCTION, self.head_processor)

        if self.config['proxy']:
            # str is required to force unicode values
            self.curl.setopt(pycurl.PROXY, str(self.config['proxy'])) 
            # CURLPROXY_HTTP, CURLPROXY_HTTP_1_0 (added in 7.19.4),
            # CURLPROXY_SOCKS4 (added in 7.15.2), CURLPROXY_SOCKS5,
            # CURLPROXY_SOCKS4A (added in 7.18.0) and CURLPROXY_SOCKS5_HOSTNAME (added in 7.18.0)
            if self.config['proxy_type']:
                ptype = getattr(pycurl, 'PROXYTYPE_%s' % self.config['proxy_type'].upper())
                self.curl.setopt(pycurl.PROXYTYPE, ptype)
            logging.debug('Using proxy %s of type %s' % (self.config['proxy'],
                self.config['proxy_type']))

        if not self.config['method']:
            if self.config['payload'] or self.config['post']:
                self.config['method'] = 'post'
            else:
                self.config['method'] = 'get'

        method = self.config['method'].lower()
        if method == 'post':
            self.curl.setopt(pycurl.POST, 1)
            if payload:
                self.curl.setopt(pycurl.POSTFIELDS, payload)
            elif post:
                post_data = urllib.urlencode(post)
                self.curl.setopt(pycurl.POSTFIELDS, post_data)
        elif method == 'put':
            self.curl.setopt(pycurl.PUT, 1)
            self.curl.setopt(pycurl.READFUNCTION, StringIO.StringIO(payload).read) 
        elif method == 'delete':
            self.curl.setopt(pycurl.CUSTOMREQUEST, 'delete')
        else:
            # Assume the GET method
            self.curl.setopt(pycurl.HTTPGET, 1)

        if self.config['headers']:
            headers = ['%s: %s' % x for x in headers.iteritems()]
            self.curl.setopt(pycurl.HTTPHEADER, headers)


    def parse_headers(self):
        for line in re.split('\r?\n', ''.join(self.response_head)):
            if not self.status_line:
                self.response_status = line
                self.response_code = line.split(' ')[0]
            try:
                name, value = line.split(': ', 1)
                if 'Set-Cookie' == name:
                    match = re.search('^([^=]+)=([^;]+)*', value)
                    if match:
                        self.cookies[match.group(1)] = match.group(2)
                else:
                    self.headers[name] = value
            except ValueError:
                pass


    def request(self):
        self.process_config()

        self.status_line = None
        self.response_head = []
        self.response_body = []
        self.headers = {}
        self.cookies = {}

        self.curl.perform()

        self.response_head = ''.join(self.response_head)
        self.response_body = ''.join(self.response_body)

        self.parse_headers()

        response = {'body': self.response_body,
                    'headers': self.headers,
                    'time': self.response_time(),
                    'code': self.response_code,
                    'curl': self.curl,
                    'status': self.response_status,
                    }

        return response


    def response_time(self):
        return self.curl.getinfo(pycurl.TOTAL_TIME)
