# Copyright: 2013, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
#import email
import logging
#import urllib
#try:
    #from cStringIO import StringIO
#except ImportError:
    #from io import BytesIO as StringIO
#import threading
import random
#try:
    #from urlparse import urlsplit, urlunsplit
#except ImportError:
    #from urllib.parse import urlsplit, urlunsplit
#import pycurl
#import tempfile
#import os.path

from grab.response import Response
from grab.tools.http import (encode_cookies, smart_urlencode, normalize_unicode,
                             normalize_http_values, normalize_post_data)
from grab.tools.user_agent import random_user_agent
from grab.base import Grab
from grab.kit import Kit

logger = logging.getLogger('grab.transport.kit')

class KitTransport(object):
    """
    Grab network transport powered with QtWebKit module
    """

    def __init__(self):
        self.kit = Kit()

    #def setup_body_file(self, storage_dir, storage_filename):
        #if storage_filename is None:
            #handle, path = tempfile.mkstemp(dir=storage_dir)
        #else:
            #path = os.path.join(storage_dir, storage_filename)
        #self.body_file = open(path, 'wb')
        #self.body_path = path

    def reset(self):
        self.request_object = {
            'url': None,
            'cookies': {},
            'method': None,
            'data': None,
            'user_agent': None,
        }
        self.response = None
        #self.response_head_chunks = []
        #self.response_body_chunks = []
        #self.response_body_bytes_read = 0
        #self.verbose_logging = False
        #self.body_file = None
        #self.body_path = None

        ## Maybe move to super-class???
        self.request_head = ''
        self.request_body = ''
        self.request_log = ''

    def process_config(self, grab):
        self.request_object['url'] = grab.config['url']
        self.request_object['method'] = grab.request_method.lower()

        if grab.config['cookiefile']:
            grab.load_cookies(grab.config['cookiefile'])

        if grab.config['cookies']:
            if not isinstance(grab.config['cookies'], dict):
                raise error.GrabMisuseError('cookies option should be a dict')
            self.request_object['cookies'] = grab.config['cookies']

        if grab.request_method == 'POST':
            if grab.config['multipart_post']:
                raise NotImplementedError
            elif grab.config['post']:
                post_data = normalize_post_data(grab.config['post'], grab.config['charset'])
            else:
                post_data = None
            self.request_object['data'] = post_data

        if grab.config['user_agent'] is None:
            if grab.config['user_agent_file'] is not None:
                with open(grab.config['user_agent_file']) as inf:
                    lines = inf.read().splitlines()
                grab.config['user_agent'] = random.choice(lines)
            else:
                pass
                # I think that it does not make sense
                # to create random user agents for webkit transport
                #grab.config['user_agent'] = random_user_agent()
        self.request_object['user_agent'] = grab.config['user_agent']

    def request(self):
        req = self.request_object
        self.kit_response = self.kit.request(
            url=req['url'],
            cookies=req['cookies'],
            method=req['method'],
            data=req['data'],
            user_agent=req['user_agent'],
        )

    def prepare_response(self, grab):
        return self.kit_response

    def extract_cookies(self):
        """
        Extract cookies.
        """

        return self.kit_response.cookies

    def __getstate__(self):
        """
        Reset curl attribute which could not be pickled.
        """
        state = self.__dict__.copy()
        state['kit'] = None
        return state

    def __setstate__(self, state):
        """
        Create pycurl instance after Grab instance was restored
        from pickled state.
        """

        state['kit'] = Kit()
        self.__dict__ = state


class GrabKit(Grab):
    def __init__(self, response_body=None, transport='grab.transport.curl.CurlTransport',
                 **kwargs):
        super(GrabKit, self).__init__(response_body=response_body,
                                       transport='grab.transport.kit.KitTransport',
                                       **kwargs)
