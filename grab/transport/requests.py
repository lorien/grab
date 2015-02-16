# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
import email
import logging
# import urllib
# try:
#    from StringIO import StringIO
# except ImportError:
#    from io import StringIO
import threading
import random
import requests 

from grab.error import GrabError, GrabMisuseError
from grab.base import UploadContent, UploadFile
from grab.response import Response
from tools.http import urlencode, normalize_http_values, normalize_unicode
from grab.util.py3k_support import *

logger = logging.getLogger('grab.transport.requests')


class RequestsTransport(object):
    def __init__(self):
        self.session = requests.session()

    def reset(self):
        # TODO: WTF???
        # Maybe move to super-class???
        self.request_headers = ''
        self.request_head = ''
        self.request_body = ''
        self.request_log = ''

        # self.request_method = None
        self.requests_config = None

    def process_config(self, grab):
        """
        Setup curl instance with values from ``grab.config``.
        """
        
        # Accumulate all request options into `self.requests_config`
        self.requests_config = {
            'headers': {},
            'payload': None,
            'cookies': None,
            'proxy': None,
        }

        if isinstance(grab.config['url'], unicode):
            grab.config['url'] = grab.config['url'].encode('utf-8')

        self.requests_config['url'] = grab.config['url']

        # self.curl.setopt(pycurl.URL, url)
        # self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        # self.curl.setopt(pycurl.MAXREDIRS, 5)
        # self.curl.setopt(pycurl.CONNECTTIMEOUT, grab.config['connect_timeout'])
        # self.curl.setopt(pycurl.TIMEOUT, grab.config['timeout'])
        # self.curl.setopt(pycurl.NOSIGNAL, 1)
        # self.curl.setopt(pycurl.WRITEFUNCTION, self.body_processor)
        # self.curl.setopt(pycurl.HEADERFUNCTION, self.head_processor)

        # User-Agent
        # TODO: move to base class
        if grab.config['user_agent'] is None:
            if grab.config['user_agent_file'] is not None:
                lines = open(grab.config['user_agent_file']).read().splitlines()
                grab.config['user_agent'] = random.choice(lines)

        # If value is None then set empty string
        # None is not acceptable because in such case
        # pycurl will set its default user agent "PycURL/x.xx.x"
        # For consistency we send empty User-Agent in case of None value
        # in all other transports too
        if not grab.config['user_agent']:
            grab.config['user_agent'] = ''
        self.requests_config['headers']['User-Agent'] = grab.config['user_agent']

        self.requests_config['method'] = grab.request_method.lower()

        if grab.request_method == 'POST' or grab.request_method == 'PUT':
            if grab.config['multipart_post']:
                raise NotImplementedError
            elif grab.config['post']:
                if isinstance(grab.config['post'], basestring):
                    # bytes-string should be posted as-is
                    # unicode should be converted into byte-string
                    if isinstance(grab.config['post'], unicode):
                        post_data = normalize_unicode(grab.config['post'])
                    else:
                        post_data = grab.config['post']
                else:
                    # dict, tuple, list should be serialized into byte-string
                    post_data = urlencode(grab.config['post'])
                self.requests_config['payload'] = post_data
                # self.curl.setopt(pycurl.POSTFIELDS, post_data)
        # elif grab.request_method == 'PUT':
            # self.curl.setopt(pycurl.PUT, 1)
            # self.curl.setopt(pycurl.READFUNCTION, StringIO(grab.config['post']).read) 
        elif grab.request_method == 'DELETE':
            pass
            # self.curl.setopt(pycurl.CUSTOMREQUEST, 'delete')
        elif grab.request_method == 'HEAD':
            pass
            # self.curl.setopt(pycurl.NOBODY, 1)
        else:
            pass
            # self.curl.setopt(pycurl.HTTPGET, 1)

        
        headers = grab.config['common_headers']
        if grab.config['headers']:
            headers.update(grab.config['headers'])
        # self.curl.setopt(pycurl.HTTPHEADER, header_tuples)
        self.requests_config['headers'].update(headers)

        # `cookiefile` option shoul be processed before `cookies` option
        # because `load_cookies` updates `cookies` option
        if grab.config['cookiefile']:
            grab.load_cookies(grab.config['cookiefile'])

        if grab.config['cookies']:
            items = normalize_http_values(grab.config['cookies'])
            self.requests_config['cookies'] = dict(items)

        # if not grab.config['reuse_cookies'] and not grab.config['cookies']:
            # self.curl.setopt(pycurl.COOKIELIST, 'ALL')

        # if grab.config['referer']:
            # self.curl.setopt(pycurl.REFERER, str(grab.config['referer']))

        # if grab.config['proxy']:
            # self.curl.setopt(pycurl.PROXY, str(grab.config['proxy'])) 
        # else:
            # self.curl.setopt(pycurl.PROXY, '')

        # if grab.config['proxy_userpwd']:
            # self.curl.setopt(pycurl.PROXYUSERPWD, grab.config['proxy_userpwd'])

        if grab.config['proxy']:
            self.requests_config['proxy'] = grab.config['proxy']

        if grab.config['proxy_userpwd']:
            raise GrabMisuseError('requests transport does not support proxy authentication')

        if grab.config['proxy_type']:
            if grab.config['proxy_type'] != 'http':
                raise GrabMisuseError('requests transport supports only proxies of http type')

    def request(self):
        try:
            cfg = self.requests_config
            func = getattr(requests, cfg['method'])
            kwargs = {}
            if cfg['payload'] is not None:
                kwargs['data'] = cfg['payload']
            if cfg['cookies'] is not None:
                kwargs['cookies'] = cfg['cookies']
            if cfg['proxy'] is not None:
                kwargs['proxies'] = {'http': cfg['proxy'],
                                     'https': cfg['proxy']}
            self._requests_response = func(
                cfg['url'], headers=cfg['headers'], **kwargs)
        except Exception as ex:
            raise GrabError(0, unicode(ex))

    def prepare_response(self, grab):
        # self.response.head = ''.join(self.response_head_chunks)
        # self.response.body = ''.join(self.response_body_chunks)
        # self.response.parse()
        # self.response.cookies = self._extract_cookies()
        # self.response.code = self.curl.getinfo(pycurl.HTTP_CODE)
        # self.response.time = self.curl.getinfo(pycurl.TOTAL_TIME)
        # self.response.url = self.curl.getinfo(pycurl.EFFECTIVE_URL)
        response = Response()
        response.head = ''

        """
        if grab.config['body_max_size'] is not None:
            chunks = []
            read_size = 0
            for chunk in self._requests_responsek
        else:
            response.body = self._requests_response.content
        """

        response.body = self._requests_response.content
        response.code = self._requests_response.status_code
        response.headers = self._requests_response.headers
        response.cookies = self._requests_response.cookies or {}
        response.url = grab.config['url']

        if grab.config['charset'] is not None:
            response.parse(charset=grab.config['charset'])
        else:
            response.parse()
        return response
