# -*- coding: utf-8 -*-
# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
"""
Exceptions:

Exception
-> GrabError
---> GrabNetworkError <- IOError 
---> DataNotFound <- IndexError
"""

import logging
import os
import urllib
from random import randint, choice
from copy import copy
import threading
from urlparse import urljoin
#from copy import deepcopy
import time
import re

from proxylist import ProxyList
from html import find_refresh_url
from response import Response

from error import GrabError, GrabNetworkError, GrabMisuseError, DataNotFound

__all__ = ('Grab', 'GrabError', 'DataNotFound', 'GrabNetworkError', 'GrabMisuseError',
           'UploadContent', 'UploadFile')

PACKAGE_DIR = os.path.dirname(os.path.realpath(__file__))

# This counter will used in enumerating network queries.
# Its value will be displayed in logging messages and also used
# in names of dumps
# I use mutable module variable to allow different
# instances of Grab maintain single counter
# This could be helpful in debuggin when your script
# creates multiple Grab instances - in case of shared counter
# grab instances do not overwrite dump logs
REQUEST_COUNTER_LOCK = threading.Lock()
GLOBAL_STATE = {'request_counter': 0}

logger = logging.getLogger('grab')

class UploadContent(str):
    """
    TODO: docstring
    """

    def __new__(cls, value):
        obj = str.__new__(cls, 'xxx')
        obj.raw_value = value
        return obj

    def field_tuple(self):
        # TODO: move to transport extension
        import pycurl
        return (pycurl.FORM_CONTENTS, self.raw_value)


class UploadFile(str):
    """
    TODO: docstring
    """

    def __new__(cls, path):
        obj = str.__new__(cls, 'xxx')
        obj.path = path
        return obj

    def field_tuple(self):
        # move to transport extension
        import pycurl
        return (pycurl.FORM_FILE, self.path)


def default_config():
    return dict(
        url = None,
        proxy = None,
        proxy_type = None,
        proxy_userpwd = None,
        post = None,
        multipart_post = None,
        #payload = None,
        method = None,
        headers = {},
        user_agent = None,
        user_agent_file = os.path.join(PACKAGE_DIR, 'user_agent.txt'),
        reuse_cookies = True,
        reuse_referer = True,
        cookies = {},
        cookiefile = None,
        referer = None,
        log_file = None,
        log_dir = False,
        follow_refresh = False,
        #nohead = False,
        nobody = False,
        body_maxsize = None,
        debug_post = False,
        # ???
        encoding = 'gzip',
        userpwd = None,
        # Timeouts
        timeout = 15,
        connect_timeout = 10,
        hammer_mode = False,
        hammer_timeouts = ((2, 5), (5, 10), (10, 20), (15, 30)),
        lowercased_tree = False,
        charset = None,
    )

#DEFAULT_EXTENSIONS = ['grab.ext.pycurl', 'grab.ext.lxml', 'grab.ext.lxml_form',
                      #'grab.ext.django', 'grab.ext.text']

import ext.lxml
import ext.lxml_form
import ext.django
import ext.text

class GrabInterface(object):
    def process_config(self):
        raise NotImplementedError

    def extract_cookies(self):
        raise NotImplementedError

    def prepare_response(self):
        raise NotImplementedError


class BaseGrab(ext.lxml.Extension,
           ext.lxml_form.Extension, ext.django.Extension,
           ext.text.Extension, GrabInterface):

    # Shortcut to grab.GrabError
    Error = GrabError

    # Attributes which should be processed when clone
    # of Grab instance is creating
    clonable_attributes = ('request_headers', 'request_head', 'request_log', 'request_body',
                           'proxylist', 'proxylist_auto_change', 'charset')

    # Info about loaded extensions
    #extensions = []
    #transport_extension = None

    """
    Public methods
    """

    def __init__(self, **kwargs):
        """
        Create Grab instance
        """

        self.config = default_config()
        self.trigger_extensions('config')
        self.default_headers = self.common_headers()
        self.trigger_extensions('init')
        self.reset()
        self.proxylist = None
        self.proxylist_auto_change = False
        self.charset = 'utf-8'
        if kwargs:
            self.setup(**kwargs)
        self.clone_counter = 0

    def reset(self):
        """
        Reset all attributes which could be modified during previous request
        or which is not initialized yet if this is the new Grab instance.

        This methods is automatically called before each network request.
        """

        self.response = Response()
        self.trigger_extensions('reset')

    def clone(self):
        """
        Create clone of Grab instance.

        Cloned instance will have the same state: cookies, referer, response data
        """

        g = self.__class__()

        #g.config = deepcopy(self.config)
        g.config = copy(self.config)
        # Apply ``copy`` function to mutable config values
        for key in ('post', 'multipart_post', 'headers', 'cookies', 'hammer_timeouts'):
            g.config[key] = copy(self.config[key])

        #cookies = self.config['cookies']
        #if self.response.cookies:
            #cookies.update(self.response.cookies)
        #g.setup(cookies=cookies)
        g.response = self.response.copy()
        for key in self.clonable_attributes:
            setattr(g, key, getattr(self, key))
        g.clone_counter = self.clone_counter + 1
        return g

    def setup(self, **kwargs):
        """
        Setting up Grab instance configuration.
        """

        for key in kwargs:
            if not key in self.config.keys():
                raise GrabMisuseError('Unknown option: %s' % key)

        if 'url' in kwargs:
            if self.config.get('url'):
                kwargs['url'] = self.make_url_absolute(kwargs['url'])
        self.config.update(kwargs)

    def go(self, url, **kwargs):
        """
        Go to ``url``

        Args:
            :url: could be absolute or relative. If relative then t will be appended to the
                absolute URL of previous request.
        """

        return self.request(url=url, **kwargs)

    def download(self, url, location, **kwargs):
        """
        Fetch document located at ``url`` and save to to ``location``.
        """

        response = self.go(url, **kwargs)
        with open(location, 'w') as out:
            out.write(response.body)
        return len(response.body)

    def prepare_request(self, **kwargs):
        """
        Configure all things to make real network request.
        This method is called before doing real request via
        tranposrt extension.
        """

        # Reset the state setted by prevous request
        self.reset()
        self.request_counter = self.get_request_counter()
        if self.proxylist_auto_change:
            self.change_proxy()
        if kwargs:
            self.setup(**kwargs)
        self.process_config()

    def request(self, **kwargs):
        """
        Perform network request.

        You can specify grab settings in ``**kwargs``.
        Any keyword argument will be passed to ``self.config``.

        Returns: ``Response`` objects.
        """

        if self.config['hammer_mode']:
            hammer_timeouts = list(self.config['hammer_timeouts'])
            connect_timeout, total_timeout = hammer_timeouts.pop(0)
            self.setup(connect_timeout=connect_timeout, timeout=total_timeout)

        while True:
            try:
                self.prepare_request(**kwargs)
                self.transport_request()
            except GrabError, ex:
                # In hammer mode try to use next timeouts
                if self.config['hammer_mode'] and ex[0] == 28:
                    # If not more timeouts
                    # then raise an error
                    if not hammer_timeouts:
                        raise
                    else:
                        connect_timeout, total_timeout = hammer_timeouts.pop(0)
                        self.setup(connect_timeout=connect_timeout, timeout=total_timeout)
                        logger.debug('Trying another timeouts. Connect: %d sec., total: %d sec.' % (connect_timeout, total_timeout))
                # If we are not in hammer mode
                # Then just raise an error
                else:
                    raise
            else:
                # Break the infinite loop in case of success response
                break

        return self.process_request_result()

    def process_request_result(self):
        """
        Process result of real request performed via transport extension.
        """

        if self.config['debug_post']:
            post = self.config['post'] or self.config['multipart_post']
            if isinstance(post, dict):
                post = post.items()
            if post:
                if isinstance(post, basestring):
                    post = post[:150] + '...'
                else:
                    post = self.normalize_http_values(post, charset='utf-8')
                    items = sorted(post, key=lambda x: x[0])
                    items = [(x[0], str(x[1])[:150]) for x in items]
                    post = '\n'.join('%-25s: %s' % x for x in items)
            if post:
                logger.debug('POST request:\n%s\n' % post)

        # It's important to delete old POST data after request is performed.
        # If POST data remains when next request will try to use them again!
        # This is not what typical user waits.

        # Disabled, see comments to repeat_request method
        #self.old_config = deepcopy(self.config) 

        self.config['post'] = None
        self.config['multipart_post'] = None
        self.config['method'] = None

        self.prepare_response()

        if self.config['reuse_cookies']:
            # Copy cookies from response into config
            # for future requests
            for name, value in self.response.cookies.items():
                #if not name in self.config['cookies']:
                    #self.config['cookies'][name] = value
                self.config['cookies'][name] = value

        # Set working charset to encode POST data of next requests
        self.charset = self.response.charset

        # TODO: raise GrabWarning if self.config['http_warnings']
        #if 400 <= self.response_code:
            #raise IOError('Response code is %s: ' % self.response_code)

        if self.config['log_file']:
            with open(self.config['log_file'], 'w') as out:
                out.write(self.response.body)

        self.save_dumps()

        if self.config['cookiefile']:
            self.dump_cookies(self.config['cookiefile'])

        if self.config['reuse_referer']:
            self.config['referer'] = self.response.url

        # TODO: check max redirect count
        if self.config['follow_refresh']:
            url = find_refresh_url(self.response.unicode_body())
            if url:
                return self.request(url=url)

        return self.response

    # Disabled due to perfomance issue
    # Who needs this method?
    #def repeat_request(self):
        #"""
        #Make the same network request again.

        #All cookies, POST data, headers will be sent again.
        #"""

        #self.config = deepcopy(self.old_config)
        #self.request()

    def sleep(self, limit1=1, limit2=None):
        """
        Sleep baby.
        
        Arguments given:
        0 - sleep for [0, 1] seconds
        1 - sleep for [0, limit1] seconds
        2 - sleep for [limit1, limit2] seconds
        """

        if limit2 is None:
            limit1, limit2 = 0, limit1
        limit1 = int(limit1 * 1000)
        limit2 = int(limit2 * 1000)
        sleep_time = randint(limit1, limit2) / 1000.0
        logger.debug('Sleeping for %f seconds' % sleep_time)
        time.sleep(sleep_time)

    def fake_response(self, content):
        # Trigger reset
        # It will reset request state and also create new
        # uninitialized response object
        self.reset()

        # Set the response body
        self.response.body = content

        # And fill other properties with reasonable empty values
        self.headers = {}
        self.status = ''
        self.response.head = ''
        self.response.parse()
        self.response.cookies = {}
        self.response.code = 200
        self.response.time = 0
        self.response.url = ''

    def setup_proxylist(self, proxy_file, proxy_type, read_timeout=None,
                        auto_init=True, auto_change=False):
        """
        Setup location of files with proxy servers

        ``proxy_file`` - file which contains list of proxy servers
        Each server could be a line of one of following formats:
        * server:port
        * server:port:username:password

        ``proxy_type`` - type of proxy servers from proxy file.
        For now all proxies should be of one type

        ``auto_init`` - if True then ``change_proxy`` method will be automatically
        called
        """

        self.proxylist = ProxyList(proxy_file, proxy_type,
                                   read_timeout=read_timeout)
        if auto_init:
            self.change_proxy()
        self.proxylist_auto_change = auto_change

    def change_proxy(self):
        """
        Set random proxy from proxylist.
        """

        server, userpwd = self.proxylist.get_random()
        self.setup(proxy=server, proxy_userpwd=userpwd,
                   proxy_type=self.proxylist.proxy_type)

    """
    Private methods
    """

    def trigger_extensions(self, event):
        for cls in self.__class__.mro()[1:]:
            if hasattr(cls, 'extra_%s' % event):
                getattr(cls, 'extra_%s' % event)(self)

    #def load_extension(self, ext_class):
        #for attr in ext_class.export_attributes:
            #self.add_to_class(attr, ext_class.__dict__[attr])
        #ext = ext_class()
        #self.extensions.append(ext)
        #if getattr(ext, 'transport', None):
            #self.transport_extension = ext

    @classmethod
    def add_to_class(cls, name, obj):
        setattr(cls, name, obj)

    def common_headers(self):
        """
        Build headers which sends typical browser.
        """

        return {
            'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.%d' % randint(2, 5),
            'Accept-Language': 'en-us,en;q=0.%d' % (randint(5, 9)),
            'Accept-Charset': 'utf-8,windows-1251;q=0.7,*;q=0.%d' % randint(5, 7),
            'Keep-Alive': '300',
            'Expect': '',
        }

    def get_request_counter(self):
        """
        Increase global request counter and return new value
        which will be used as request number for current request.
        """

        # TODO: do not use lock in main thread
        REQUEST_COUNTER_LOCK.acquire()
        GLOBAL_STATE['request_counter'] += 1
        counter = GLOBAL_STATE['request_counter']
        REQUEST_COUNTER_LOCK.release()
        return counter

    def save_dumps(self):
        if self.config['log_dir']:
            tname = threading.currentThread().getName().lower()
            if tname == 'mainthread':
                tname = ''
            else:
                tname = '-%s' % tname
            fname = os.path.join(self.config['log_dir'], '%02d%s.log' % (self.request_counter, tname))
            with open(fname, 'w') as out:
                out.write('Request:\n')
                out.write(self.request_head)
                out.write('\n')
                out.write('Response:\n')
                out.write(self.response.head)

            fext = 'html'
            #dirs = self.response_url().split('//')[1].strip().split('/')
            #if len(dirs) > 1:
                #fext = dirs[-1].split('.')[-1]
                
            fname = os.path.join(self.config['log_dir'], '%02d%s.%s' % (self.request_counter, tname, fext))
            with open(fname, 'w') as out:
                out.write(self.response.body)

    def urlencode(self, items):
        """
        Convert sequence of items into bytestring which could be submitted
        in POST or GET request.

        ``items`` could dict or tuple or list.
        """

        if isinstance(items, dict):
            items = items.items()
        return urllib.urlencode(self.normalize_http_values(items))


    def encode_cookies(self, items, join=True):
        """
        Serialize dict or sequence of two-element items into string suitable
        for sending in Cookie http header.
        """

        def encode(val):
            """
            URL-encode special characters in the text.

            In cookie value only ",", " ", "\t" and ";" should be encoded
            """

            return val.replace(' ', '%20').replace('\t', '%09')\
                      .replace(';', '%3B').replace(',', '%2C')

        if isinstance(items, dict):
            items = items.items()
        items = self.normalize_http_values(items)
        tokens = []
        for key, value in items:
            tokens.append('%s=%s' % (encode(key), encode(value)))
        if join:
            return '; '.join(tokens)
        else:
            return tokens


    def normalize_http_values(self, items, charset=None):
        """
        Accept sequence of (key, value) paris and convert each
        value into bytestring.

        Unicode is converted into bytestring using charset of previous response
        (or utf-8, if no requests were performed)

        None is converted into empty string. 

        Instances of ``UploadContent`` or ``UploadFile`` is converted
        into special pycurl objects.
        """

        def process(item):
            key, value = item

            # normalize value
            if isinstance(value, (UploadContent, UploadFile)):
                value = value.field_tuple()
            elif isinstance(value, unicode):
                value = self.normalize_unicode(value, charset=charset)
            elif value is None:
                value = ''

            # normalize key
            if isinstance(key, unicode):
                key = self.normalize_unicode(key, charset=charset)

            return key, value

        return map(process, items)

    def normalize_unicode(self, value, charset=None):
        """
        Convert unicode into byte-string using detected charset (default or from
        previous response)

        By default, charset from previous response is used to encode unicode into
        byte-string but you can enforce charset with ``charset`` option
        """

        if not isinstance(value, unicode):
            raise GrabMisuseError('normalize_unicode method accepts only unicode values')
        return value.encode(self.charset if charset is None else charset, 'ignore')

    def make_url_absolute(self, url):
        """
        Make url absolute using previous request url as base url.
        """

        if self.config['url']:
            return urljoin(self.config['url'], url)
        else:
            return url

    def clear_cookies(self):
        """
        Clear all cookies.
        """

        self.config['cookies'] = {}
