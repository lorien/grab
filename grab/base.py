# -*- coding: utf-8 -*-
# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
"""
The core of grab package: the Grab class.
"""
from __future__ import absolute_import
import logging
import os
import urllib
from random import randint, choice
from copy import copy
import threading
from urlparse import urljoin
import time
import re
import json

from .proxylist import ProxyList, parse_proxyline
from .tools.html import find_refresh_url, find_base_url
from .response import Response
from . import error
from .upload import UploadContent, UploadFile
from .tools.http import normalize_http_values
from .extension import ExtensionManager

# This counter will used in enumerating network queries.
# Its value will be displayed in logging messages and also used
# in names of dumps
# I use mutable module variable to allow different
# instances of Grab maintain single counter
# This could be helpful in debuggin when your script
# creates multiple Grab instances - in case of shared counter
# grab instances do not overwrite dump logs
REQUEST_COUNTER_LOCK = threading.Lock()
GLOBAL_STATE = {
    'request_counter': 0,
    'dom_build_time': 0,
}

# Some extensions need GLOBAL_STATE variable
# what's why they go after GLOBAL_STATE definition
from .ext.lxml import LXMLExtension
from .ext.form import FormExtension
from .ext.django import DjangoExtension
from .ext.text import TextExtension
from .ext.rex import RegexpExtension
from .ext.pquery import PyqueryExtension
from .ext.ftp import FTPExtension

__all__ = ('Grab', 'UploadContent', 'UploadFile')

MUTABLE_CONFIG_KEYS = ['post', 'multipart_post', 'headers', 'cookies',
                       'hammer_timeouts']

logger = logging.getLogger('grab.base')

# Logger to handle network activity
# It is separate logger to allow you easily
# control network logging separately from other grab logs
logger_network = logging.getLogger('grab.network')

def copy_config(config, mutable_config_keys=MUTABLE_CONFIG_KEYS):
    """
    Copy grab config ojection with correct handling
    of mutable config values.
    """

    cloned_config = copy(config)
    # Apply ``copy`` function to mutable config values
    for key in mutable_config_keys:
        cloned_config[key] = copy(config[key])
    return cloned_config


def default_config():
    # TODO: it seems config should be splitted into two entities:
    # 1) config which is not changed during request
    # 2) changable config
    return dict(
        # Common
        url = None,

        # Debugging
        log_file = None,
        log_dir = False,
        debug_post = False,
        # Only for curl transport
        verbose_logging = False,

        # Proxy
        proxy = None,
        proxy_type = None,
        proxy_userpwd = None,

        # Method, Post
        method = None,
        post = None,
        multipart_post = None,

        # Headers, User-Agent, Referer
        headers = {},
        common_headers = {},
        user_agent = None,
        user_agent_file = None,
        referer = None,
        reuse_referer = True,

        # Cookies
        cookies = {},
        reuse_cookies = True,
        cookiefile = None,

        # Timeouts
        timeout = 15,
        connect_timeout = 10,
        hammer_mode = False,
        hammer_timeouts = ((2, 5), (5, 10), (10, 20), (15, 30)),

        # Response processing
        nobody = False,
        body_maxsize = None,

        # Content compression
        encoding = 'gzip',

        # Редиректы
        follow_refresh = False,
        follow_location = True,
        redirect_limit = 5,

        # Authentication
        userpwd = None,

        # Character set to which any unicode data should be encoded
        # before get placed in request
        # This setting is overwritten after each request with
        # charset of rertreived document
        charset = 'utf-8',
        # Charset to use for converting content of response
        # into unicode, by default it is detected automatically
        document_charset = None,

        # Convert document body to lower case before bulding LXML tree
        # It does not affect `response.body`
        lowercased_tree = False,

        # Strip null bytes from document body before building lXML tree
        # It does not affect `response.body`
        strip_null_bytes = True,

        # Strip XML declaration before building unicode body
        strip_xml_declaration = True,
    )


class Grab(LXMLExtension, FormExtension, PyqueryExtension,
           DjangoExtension, TextExtension, RegexpExtension,
           FTPExtension):

    __metaclass__ = ExtensionManager

    # Points which could be handled in extension classes
    extension_points = ('config', 'init', 'reset')

    # Attributes which should be processed when clone
    # of Grab instance is creating
    clonable_attributes = ('request_head', 'request_log', 'request_body',
                           'proxylist', 'proxylist_auto_change')

    # Complex config items which points to mutable objects
    mutable_config_keys = copy(MUTABLE_CONFIG_KEYS)

    """
    Public methods
    """

    def __init__(self, transport='curl.CurlTransport', response_body=None,
                 **kwargs):
        """
        Create Grab instance
        """

        self.config = default_config()
        self.config['common_headers'] = self.common_headers()
        self.trigger_extensions('config')
        self.trigger_extensions('init')
        self._request_prepared = False

        self.transport_name = transport
        mod_name, cls_name = transport.split('.')
        mod = __import__('grab.transport.%s' % mod_name, globals(),
                         locals(), ['foo'])
        self.transport = getattr(mod, cls_name)()

        self.reset()
        self.proxylist = None
        self.proxylist_auto_change = False
        if kwargs:
            self.setup(**kwargs)
        self.clone_counter = 0
        if response_body is not None:
            self.fake_response(response_body)

    def reset(self):
        """
        Reset all attributes which could be modified during previous request
        or which is not initialized yet if this is the new Grab instance.

        This methods is automatically called before each network request.
        """

        self.response = None

        self.request_head = None
        self.request_log = None
        self.request_body = None

        self.request_method = None
        self.trigger_extensions('reset')
        self.transport.reset()

    def clone(self, **kwargs):
        """
        Create clone of Grab instance.

        Cloned instance will have the same state: cookies, referer, response data

        :param **kwargs: overrides settings of cloned grab instance
        """

        g = Grab(transport=self.transport_name)
        g.config = self.dump_config()

        if self.response is not None:
            g.response = self.response.copy()
        for key in self.clonable_attributes:
            setattr(g, key, getattr(self, key))
        g.clone_counter = self.clone_counter + 1

        if kwargs:
            g.setup(**kwargs)

        return g

    def adopt(self, g):
        """
        Copy the state of another `Grab` instance.

        Use case: create backup of current state to the cloned instance and
        then restore the state from it.
        """

        self.load_config(g.config)
        if g.response is not None:
            self.response = g.response.copy()
        for key in self.clonable_attributes:
            setattr(self, key, getattr(g, key))
        self.clone_counter = g.clone_counter + 1

    def dump_config(self):
        """
        Make clone of current config.
        """

        return copy_config(self.config, self.mutable_config_keys)

    def load_config(self, config):
        """
        Configure grab instance with external config object.
        """

        self.config = copy_config(config, self.mutable_config_keys)

    def setup(self, **kwargs):
        """
        Setting up Grab instance configuration.
        """

        for key in kwargs:
            if not key in self.config.keys():
                raise error.GrabMisuseError('Unknown option: %s' % key)

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
        with open(location, 'wb') as out:
            out.write(response.body)
        return len(response.body)

    def prepare_request(self, **kwargs):
        """
        Configure all things to make real network request.
        This method is called before doing real request via
        tranposrt extension.
        """

        # Reset the state setted by previous request
        if not self._request_prepared:
            self.reset()
            self.request_counter = self.get_request_counter()
            if self.proxylist_auto_change:
                self.change_proxy()
            if kwargs:
                self.setup(**kwargs)
            self.request_method = self.detect_request_method()
            self.transport.process_config(self)
            self._request_prepared = True

    def log_request(self, extra=''):
        """
        Send request details to logging system.
        """

        tname = threading.currentThread().getName().lower()
        if tname == 'mainthread':
            tname = ''
        else:
            tname = '-%s' % tname

        if self.config['proxy']:
            if self.config['proxy_userpwd']:
                auth = ' with authorization'
            else:
                auth = ''
            proxy_info = ' via %s proxy of type %s%s' % (
                self.config['proxy'], self.config['proxy_type'], auth)
        else:
            proxy_info = ''
        if extra:
            extra = '[%s] ' % extra
        logger_network.debug('[%02d%s] %s%s %s%s' % (
            self.request_counter, tname,
            extra, self.request_method,
            self.config['url'], proxy_info))

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
                self.log_request()
                self.transport.request()
            except error.GrabError, ex:

                # In hammer mode try to use next timeouts
                if self.config['hammer_mode'] and isinstance(ex, (error.GrabTimeoutError,
                                                                  error.GrabConnectionError)):
                    # If not more timeouts
                    # then raise an error
                    if not hammer_timeouts:
                        self._request_prepared = False
                        raise
                    else:
                        connect_timeout, total_timeout = hammer_timeouts.pop(0)
                        self.setup(connect_timeout=connect_timeout, timeout=total_timeout)
                        logger_network.debug('Trying another timeouts. Connect: %d sec., total: %d sec.' % (connect_timeout, total_timeout))
                        self._request_prepared = False
                # If we are not in hammer mode
                # Then just raise an error
                else:
                    self._request_prepared = False
                    raise
            else:
                # Break the infinite loop in case of success response
                break

        # It will configure `self.response`
        self.process_request_result()

        return self.response

    def process_request_result(self, prepare_response_func=None):
        """
        Process result of real request performed via transport extension.
        """

        # TODO: move into separate method
        if self.config['debug_post']:
            post = self.config['post'] or self.config['multipart_post']
            if isinstance(post, dict):
                post = post.items()
            if post:
                if isinstance(post, basestring):
                    post = post[:150] + '...'
                else:
                    post = normalize_http_values(post, charset='utf-8')
                    items = sorted(post, key=lambda x: x[0])
                    new_items = []
                    for key, value in items:
                        if len(value) > 150:
                            value = value[:150] + '...'
                        else:
                            value = value
                        new_items.append((key, value))
                    post = '\n'.join('%-25s: %s' % x for x in new_items)
            if post:
                logger_network.debug('POST request:\n%s\n' % post)

        # It's important to delete old POST data after request is performed.
        # If POST data is not cleared then next request will try to use them again!

        self.config['post'] = None
        self.config['multipart_post'] = None
        self.config['method'] = None

        if prepare_response_func:
            self.response = prepare_response_func(self.transport, self)
        else:
            self.response = self.transport.prepare_response(self)

        self.config['charset'] = self.response.charset

        if self.config['reuse_cookies']:
            # Copy cookies from response into config object
            for name, value in self.response.cookies.items():
                self.config['cookies'][name] = value

        # TODO: raise GrabWarning if self.config['http_warnings']
        #if 400 <= self.response_code:
            #raise IOError('Response code is %s: ' % self.response_code)

        if self.config['log_file']:
            with open(self.config['log_file'], 'w') as out:
                out.write(self.response.body)


        if self.config['cookiefile']:
            self.dump_cookies(self.config['cookiefile'])

        if self.config['reuse_referer']:
            self.config['referer'] = self.response.url

        self.copy_request_data()

        # Should be called after `copy_request_data`
        self.save_dumps()

        self._request_prepared = False

        # TODO: check max redirect count
        if self.config['follow_refresh']:
            url = find_refresh_url(self.response.unicode_body(
                strip_xml_declaration=self.config['strip_xml_declaration']))
            if url:
                return self.request(url=url)

        return None

    def copy_request_data(self):
        # TODO: Maybe request object?
        self.request_head = self.transport.request_head
        self.request_body = self.transport.request_body
        self.request_log = self.transport.request_log

    def sleep(self, *args, **kwargs):
        """
        See grab.tools.control.sleep
        """

        logger.debug('Grab.sleep method is depricated. Use grab.tools.control.sleep method instead.')
        from grab.tools.control import sleep
        sleep(*args, **kwargs)

    def fake_response(self, content, **kwargs):
        """
        Setup `response` object without real network requests.

        Useful for testing and debuging.

        All ``**kwargs`` will be passed to `Response` constructor.
        """

        # Trigger reset
        self.reset()

        # Configure fake response object
        res = Response()
        res.body = content
        res.status = ''
        res.head = ''
        res.parse(charset=kwargs.get('document_charset'))
        res.cookies = {}
        res.code = 200
        res.time = 0
        res.url = ''

        for key, value in kwargs.items():
            setattr(res, key, value)

        self.response = res

    def setup_proxylist(self, proxy_file=None, proxy_type='http', read_timeout=None,
                        auto_init=True, auto_change=False,
                        server_list=None):
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

        self.proxylist = ProxyList(proxy_file=proxy_file, proxy_type=proxy_type,
                                   server_list=server_list, read_timeout=read_timeout)
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
            fname = os.path.join(self.config['log_dir'], '%02d%s.log' % (
                self.request_counter, tname))
            with open(fname, 'w') as out:
                out.write('Request:\n')
                out.write(self.request_head)
                out.write('\n')
                out.write('Response:\n')
                out.write(self.response.head)

            fext = 'html'
            fname = os.path.join(self.config['log_dir'], '%02d%s.%s' % (
                self.request_counter, tname, fext))
            self.response.save(fname)

    def make_url_absolute(self, url, resolve_base=False):
        """
        Make url absolute using previous request url as base url.
        """

        if self.config['url']:
            if resolve_base:
                base_url = find_base_url(self.response.unicode_body())
                if base_url:
                    return urljoin(base_url, url)
            return urljoin(self.config['url'], url)
        else:
            return url

    def detect_request_method(self):
        """
        Analize request config and find which
        request method will be used.

        Returns request method in upper case
        
        This method needs simetime when process_config method
        was not executed yet.
        """

        method = self.config['method']
        if method:
            method = method.upper()
        else:
            if self.config['post'] or self.config['multipart_post']:
                method = 'POST'
            else:
                method = 'GET'
        return method

    def clear_cookies(self):
        """
        Clear all remembered cookies.
        """

        self.config['cookies'] = {}

    def load_cookies(self, path):
        """
        Load cookies from the file.

        Content of file should be a JSON-serialized dict of keys and values.
        """

        with open(path) as inf:
            data = inf.read()
            if data:
                cookies = json.loads(data)
            else:
                cookies = {}
        self.config['cookies'].update(cookies)

    def dump_cookies(self, path):
        """
        Dump all cookies to file.

        Cookies are dumped as JSON-serialized dict of keys and values.
        """

        with open(path, 'w') as out:
            out.write(json.dumps(self.config['cookies']))

    def setup_with_proxyline(self, line, proxy_type='http'):
        host, port, user, pwd = parse_proxyline(line)
        server_port = '%s:%s' % (host, port)
        self.setup(proxy=server_port, proxy_type=proxy_type)
        if user:
            userpwd = '%s:%s' % (user, pwd)
            self.setup(proxy_userpwd=userpwd)

    def __getstate__(self):
        """
        Reset cached lxml objects which could not be pickled.
        """
        state = self.__dict__.copy()
        state['_lxml_form'] = None
        state['_lxml_tree'] = None
        state['_strict_lxml_tree'] = None
        return state

    @property
    def request_headers(self):
        """
        Temporary hack till the time I'll understand
        where to store request details.
        """


        head = self.request_head
        pos = head.find('\n')
        if pos > -1:
            head = head[pos:]
        return email.message_from_string(text[pos:])


# For backward compatibility
BaseGrab = Grab
