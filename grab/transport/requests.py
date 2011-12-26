# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
from __future__ import absolute_import
import email
import logging
import urllib
from StringIO import StringIO
import threading
import random

from ..base import GrabError, GrabMisuseError, UploadContent, UploadFile

logger = logging.getLogger('grab')

class RequestsTransportExtension(object):
    def extra_init(self):
        import requests 

        self.session = requests.session()

    def extra_reset(self):
        #self.response_head_chunks = []
        #self.response_body_chunks = []
        #self.response_body_bytes_read = 0
        self.request_headers = ''
        self.request_head = ''
        self.request_log = ''
        self.request_body = ''
        self.request_method = None
        self.requests_config = None

    #def head_processor(self, chunk):
        #"""
        #Process head of response.
        #"""

        #if self.config['nohead']:
            #return 0
        #self.response_head_chunks.append(chunk)
        ## Returning None implies that all bytes were written
        #return None

    #def body_processor(self, chunk):
        #"""
        #Process body of response.
        #"""

        #if self.config['nobody']:
            #return 0
        #self.response_body_chunks.append(chunk)
        ## Returning None implies that all bytes were written
        #return None

    #def debug_processor(self, _type, text):
        #"""
        #Parse request headers and save to ``self.request_headers``

        #0: CURLINFO_TEXT
        #1: CURLINFO_HEADER_IN
        #2: CURLINFO_HEADER_OUT
        #3: CURLINFO_DATA_IN
        #4: CURLINFO_DATA_OUT
        #5: CURLINFO_unrecognized_type
        #"""

        #if _type == pycurl.INFOTYPE_HEADER_OUT:
            #self.request_head += text
            #lines = text.splitlines()
            #text = '\n'.join(lines[1:])
            #self.request_headers = dict(email.message_from_string(text))

        #if _type == pycurl.INFOTYPE_DATA_OUT:
            #self.request_body += text

        #if _type == pycurl.INFOTYPE_TEXT:
            #if self.request_log is None:
                #self.request_log = ''
            #self.request_log += text

    def process_config(self):
        """
        Setup curl instance with values from ``self.config``.
        """
        
        # Accumulate all request options into `self.requests_config`
        self.requests_config = {'headers': {}, 'payload': None,
                                'cookies': None, 'proxy': None}

        if isinstance(self.config['url'], unicode):
            self.config['url'] = self.config['url'].encode('utf-8')

        self.requests_config['url'] = self.config['url']

        #self.curl.setopt(pycurl.URL, url)
        #self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        #self.curl.setopt(pycurl.MAXREDIRS, 5)
        #self.curl.setopt(pycurl.CONNECTTIMEOUT, self.config['connect_timeout'])
        #self.curl.setopt(pycurl.TIMEOUT, self.config['timeout'])
        #self.curl.setopt(pycurl.NOSIGNAL, 1)
        #self.curl.setopt(pycurl.WRITEFUNCTION, self.body_processor)
        #self.curl.setopt(pycurl.HEADERFUNCTION, self.head_processor)

        # User-Agent
        # TODO: move to base class
        if self.config['user_agent'] is None:
            if self.config['user_agent_file'] is not None:
                lines = open(self.config['user_agent_file']).read().splitlines()
                self.config['user_agent'] = random.choice(lines)

        # If value is None then set empty string
        # None is not acceptable because in such case
        # pycurl will set its default user agent "PycURL/x.xx.x"
        # For consistency we send empty User-Agent in case of None value
        # in all other transports too
        if not self.config['user_agent']:
            self.config['user_agent'] = ''
        self.requests_config['headers']['User-Agent'] = self.config['user_agent']

        #if self.config['debug']:
            #self.curl.setopt(pycurl.VERBOSE, 1)
            #self.curl.setopt(pycurl.DEBUGFUNCTION, self.debug_processor)

        ## Ignore SSL errors
        #self.curl.setopt(pycurl.SSL_VERIFYPEER, 0)
        #self.curl.setopt(pycurl.SSL_VERIFYHOST, 0)

        self.requests_config['method'] = self.request_method.lower()

        if self.request_method == 'POST' or self.request_method == 'PUT':
            if self.config['multipart_post']:
                raise NotImplementedError
                #if isinstance(self.config['multipart_post'], basestring):
                    #raise GrabMisuseError('multipart_post option could not be a string')
                #post_items = self.normalize_http_values(self.config['multipart_post'])
                #self.curl.setopt(pycurl.HTTPPOST, post_items) 
            elif self.config['post']:
                if isinstance(self.config['post'], basestring):
                    # bytes-string should be posted as-is
                    # unicode should be converted into byte-string
                    if isinstance(self.config['post'], unicode):
                        post_data = self.normalize_unicode(self.config['post'])
                    else:
                        post_data = self.config['post']
                else:
                    # dict, tuple, list should be serialized into byte-string
                    post_data = self.urlencode(self.config['post'])
                self.requests_config['payload'] = post_data
                #self.curl.setopt(pycurl.POSTFIELDS, post_data)
        #elif self.request_method == 'PUT':
            #self.curl.setopt(pycurl.PUT, 1)
            #self.curl.setopt(pycurl.READFUNCTION, StringIO(self.config['post']).read) 
        elif self.request_method == 'DELETE':
            pass
            #self.curl.setopt(pycurl.CUSTOMREQUEST, 'delete')
        elif self.request_method == 'HEAD':
            pass
            #self.curl.setopt(pycurl.NOBODY, 1)
        else:
            pass
            #self.curl.setopt(pycurl.HTTPGET, 1)

        
        headers = self.default_headers
        if self.config['headers']:
            headers.update(self.config['headers'])
        #header_tuples = [str('%s: %s' % x) for x\
                         #in headers.iteritems()]
        #self.curl.setopt(pycurl.HTTPHEADER, header_tuples)
        self.requests_config['headers'].update(headers)

        if self.config['cookies']:
            items = self.normalize_http_values(self.config['cookies'])
            self.requests_config['cookies'] = dict(items)

        #if not self.config['reuse_cookies'] and not self.config['cookies']:
            #self.curl.setopt(pycurl.COOKIELIST, 'ALL')

        if self.config['cookiefile']:
            self.load_cookies(self.config['cookiefile'])


        #if self.config['referer']:
            #self.curl.setopt(pycurl.REFERER, str(self.config['referer']))

        #if self.config['proxy']:
            #self.curl.setopt(pycurl.PROXY, str(self.config['proxy'])) 
        #else:
            #self.curl.setopt(pycurl.PROXY, '')

        #if self.config['proxy_userpwd']:
            #self.curl.setopt(pycurl.PROXYUSERPWD, self.config['proxy_userpwd'])

        if self.config['proxy']:
            self.requests_config['proxy'] = self.config['proxy']

        if self.config['proxy_userpwd']:
            raise GrabMisuseError('requests transport does not support proxy authentication')

        if self.config['proxy_type']:
            if self.config['proxy_type'] != 'http':
                raise GrabMisuseError('requests transport supports only proxies of http type')

        #if self.config['encoding']:
            #self.curl.setopt(pycurl.ENCODING, self.config['encoding'])

        #if self.config['userpwd']:
            #self.curl.setopt(pycurl.USERPWD, self.config['userpwd'])

        #if self.config['charset']:
            #self.charset = self.config['charset']

    #def extract_cookies(self):
        #"""
        #Extract cookies.
        #"""

        ## Example of line:
        ## www.google.com\tFALSE\t/accounts/\tFALSE\t0\tGoogleAccountsLocale_session\ten
        #cookies = {}
        #for line in self.curl.getinfo(pycurl.INFO_COOKIELIST):
            #chunks = line.split('\t')
            #cookies[chunks[-2]] = chunks[-1]
        #return cookies


    def transport_request(self):
        import requests
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
        except Exception, ex:
            raise GrabError(0, unicode(ex))

    def prepare_response(self):
        #self.response.head = ''.join(self.response_head_chunks)
        #self.response.body = ''.join(self.response_body_chunks)
        #self.response.parse()
        #self.response.cookies = self.extract_cookies()
        #self.response.code = self.curl.getinfo(pycurl.HTTP_CODE)
        #self.response.time = self.curl.getinfo(pycurl.TOTAL_TIME)
        #self.response.url = self.curl.getinfo(pycurl.EFFECTIVE_URL)
        self.response.head = ''
        self.response.body = self._requests_response.content
        self.response.code = self._requests_response.status_code
        self.response.headers = self._requests_response.headers
        self.response.cookies = self._requests_response.cookies or {}
        self.response.url = self.config['url']

    #def load_cookies(self, path):
        #"""
        #Load cookies from the file.

        #The cookie data may be in Netscape / Mozilla cookie data format or just regular HTTP-style headers dumped to a file.
        #"""

        #self.curl.setopt(pycurl.COOKIEFILE, path)


    #def dump_cookies(self, path):
        #"""
        #Dump all cookies to file.

        #Each cookie is dumped in the format:
        ## www.google.com\tFALSE\t/accounts/\tFALSE\t0\tGoogleAccountsLocale_session\ten
        #"""

        #open(path, 'w').write('\n'.join(self.curl.getinfo(pycurl.INFO_COOKIELIST)))

    #def clear_cookies(self):
        #"""
        #Clear all cookies.
        #"""

        ## Write tests
        #self.curl.setopt(pycurl.COOKIELIST, 'ALL')
        #self.config['cookies'] = {}
        #self.response.cookies = None

    #def reset_curl_instance(self):
        #"""
        #Completely recreate curl instance from scratch.
        
        #I add this method because I am not sure that
        #``clear_cookies`` method works fine and I should be sure
        #I can reset all cokies.
        #"""

        #self.curl = pycurl.Curl()


from ..base import BaseGrab
class GrabRequests(RequestsTransportExtension, BaseGrab):
    pass
