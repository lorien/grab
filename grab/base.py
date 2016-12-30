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
from random import randint
from copy import copy, deepcopy
import threading
import itertools
import collections
from six.moves.urllib.parse import urljoin
import email
from datetime import datetime
import weakref
import six
from weblib.html import find_base_url
from weblib.http import normalize_http_values

from grab.document import Document
from grab import error
from grab.cookie import CookieManager
from grab.proxylist import ProxyList, parse_proxy_line
from grab.deprecated import DeprecatedThings
from grab.util.warning import warn

__all__ = ('Grab',)
# This counter will used in enumerating network queries.
# Its value will be displayed in logging messages and also used
# in names of dumps
# I use mutable module variable to allow different
# instances of Grab to maintain single counter
# This could be helpful in debugging when your script
# creates multiple Grab instances - in case of shared counter
# grab instances do not overwrite dump logs
REQUEST_COUNTER = itertools.count(1)
GLOBAL_STATE = {
    'dom_build_time': 0,
}
MUTABLE_CONFIG_KEYS = ['post', 'multipart_post', 'headers', 'cookies']
TRANSPORT_CACHE = {}
TRANSPORT_ALIAS = {
    'pycurl': 'grab.transport.curl.CurlTransport',
    'urllib3': 'grab.transport.urllib3.Urllib3Transport',
}

logger = logging.getLogger('grab.base')
# Logger to handle network activity
# It is done as separate logger to allow you easily
# control network logging separately from other grab logs
logger_network = logging.getLogger('grab.network')


def reset_request_counter():
    global REQUEST_COUNTER

    REQUEST_COUNTER = itertools.count(1)


def copy_config(config, mutable_config_keys=MUTABLE_CONFIG_KEYS):
    """
    Copy grab config with correct handling of mutable config values.
    """

    cloned_config = copy(config)
    # Apply ``copy`` function to mutable config values
    for key in mutable_config_keys:
        cloned_config[key] = copy(config[key])
    return cloned_config


def default_config():
    # TODO: Maybe config should be splitted into two entities:
    # 1) config which is not changed during request
    # 2) changeable settings
    return dict(
        # Common
        url=None,

        # Debugging
        log_file=None,
        log_dir=False,
        debug_post=False,
        debug_post_limit=150,
        # Only for curl transport
        debug=False,
        verbose_logging=False,

        # Only for selenium transport
        webdriver='firefox',
        selenium_wait=1,  # in seconds

        # Proxy
        proxy=None,
        proxy_type=None,
        proxy_userpwd=None,
        proxy_auto_change=True,

        # Method, Post
        method=None,
        post=None,
        multipart_post=None,

        # Headers, User-Agent, Referer
        headers={},
        common_headers={},
        user_agent=None,
        user_agent_file=None,
        referer=None,
        reuse_referer=True,

        # Cookies
        cookies={},
        reuse_cookies=True,
        cookiefile=None,

        # Timeouts
        timeout=15,
        connect_timeout=3,

        # Connection
        connection_reuse=True,

        # Response processing
        nobody=False,
        body_maxsize=None,
        body_inmemory=True,
        body_storage_dir=None,
        body_storage_filename=None,
        body_storage_create_dir=False,
        reject_file_size=None,

        # Content compression
        encoding='gzip',

        # Network interface
        interface=None,

        # Redirects
        follow_refresh=False,
        follow_location=True,
        redirect_limit=10,

        # Authentication
        userpwd=None,

        # Character set to which any unicode data should be encoded
        # before get placed in request
        # This setting is overwritten after each request with
        # charset of retrieved document
        charset='utf-8',

        # Charset to use for converting content of response
        # into unicode, by default it is detected automatically
        document_charset=None,

        # Content type control how DOM are built
        # For html type HTML DOM builder is used
        # For xml type XML DOM builder is used
        content_type='html',

        # Fix &#X; entities, where X between 128 and 160
        # Such entities are parsed by modern browsers as
        # windows-1251 entities independently of the real charset of
        # the document, If this option is True then such entities
        # will be replaced with correct unicode entities e.g.:
        # &#151; ->  &#8212;
        fix_special_entities=True,

        # Convert document body to lower case before building LXML tree
        # It does not affect `self.doc.body`
        lowercased_tree=False,

        # Strip null bytes from document body before building lXML tree
        # It does not affect `self.doc.body`
        strip_null_bytes=True,

        # Internal object to store
        state={},
    )


class Grab(DeprecatedThings):

    __slots__ = ('request_head', 'request_body',
                 #'request_log',
                 'proxylist', 'config',
                 'transport',
                 'transport_param', 'request_method', 'request_counter',
                 '__weakref__', 'cookies',
                 'meta',

                 # Dirty hack to make it possible to inherit Grab from
                 # multiple base classes with __slots__
                 '_doc',
                 )

    # Attributes which should be processed when clone
    # of Grab instance is creating
    clonable_attributes = ('request_head', 'request_body',
                           #'request_log',
                           'proxylist')

    # Complex config items which points to mutable objects
    mutable_config_keys = copy(MUTABLE_CONFIG_KEYS)

    """
    Public methods
    """

    def __init__(self, document_body=None,
                 transport='pycurl', **kwargs):
        """
        Create Grab instance
        """

        self.meta = {}
        self._doc = None
        self.config = default_config()
        self.config['common_headers'] = self.common_headers()
        self.cookies = CookieManager()
        self.proxylist = ProxyList()
        self.setup_transport(transport)
        self.reset()
        if kwargs:
            self.setup(**kwargs)
        if document_body is not None:
            self.setup_document(document_body)

    def _get_doc(self):
        if self._doc is None:
            self._doc = Document(self)
        return self._doc

    def _set_doc(self, obj):
        self._doc = obj

    doc = property(_get_doc, _set_doc)

    def setup_transport(self, transport_param):
        self.transport_param = transport_param
        if isinstance(transport_param, six.string_types):
            if transport_param in TRANSPORT_ALIAS:
                transport_param = TRANSPORT_ALIAS[transport_param]
            if not '.' in transport_param:
                raise error.GrabMisuseError('Unknown transport: %s'
                                            % transport_param)
            else:
                mod_path, cls_name = transport_param.rsplit('.', 1)
                try:
                    cls = TRANSPORT_CACHE[(mod_path, cls_name)]
                except KeyError:
                    mod = __import__(mod_path, globals(), locals(), ['foo'])
                    cls = getattr(mod, cls_name)
                    TRANSPORT_CACHE[(mod_path, cls_name)] = cls
                self.transport = cls()
        elif isinstance(transport_param, collections.Callable):
            self.transport = transport_param()
        else:
            raise error.GrabMisuseError('Option `transport` should be string '
                                        'or callable. Got %s'
                                        % type(transport_param))

    def reset(self):
        """
        Reset all attributes which could be modified during previous request
        or which is not initialized yet if this is the new Grab instance.

        This methods is automatically called before each network request.
        """

        self.request_head = None
        #self.request_log = None
        self.request_body = None
        self.request_method = None
        self.transport.reset()

    def clone(self, **kwargs):
        """
        Create clone of Grab instance.

        Cloned instance will have the same state: cookies, referrer, response
        document data

        :param **kwargs: overrides settings of cloned grab instance
        """

        g = Grab(transport=self.transport_param)
        g.config = self.dump_config()

        g.doc = self.doc.copy()
        g.doc.grab = weakref.proxy(g)

        for key in self.clonable_attributes:
            setattr(g, key, getattr(self, key))
        g.cookies = deepcopy(self.cookies)

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

        self.doc = g.doc.copy(new_grab=self)

        for key in self.clonable_attributes:
            setattr(self, key, getattr(g, key))
        self.cookies = deepcopy(g.cookies)

    def dump_config(self):
        """
        Make clone of current config.
        """

        conf = copy_config(self.config, self.mutable_config_keys)
        conf['state'] = {
            'cookiejar_cookies': list(self.cookies.cookiejar),
        }
        return conf

    def load_config(self, config):
        """
        Configure grab instance with external config object.
        """

        self.config = copy_config(config, self.mutable_config_keys)
        if 'cookiejar_cookies' in config['state']:
            self.cookies = CookieManager.from_cookie_list(
                config['state']['cookiejar_cookies'])

    def setup(self, **kwargs):
        """
        Setting up Grab instance configuration.
        """

        if 'hammer_mode' in kwargs:
            warn('Option `hammer_mode` is deprecated. Grab does not '
                 'support hammer mode anymore.')
            del kwargs['hammer_mode']

        if 'hammer_timeouts' in kwargs:
            warn('Option `hammer_timeouts` is deprecated. Grab does not '
                 'support hammer mode anymore.')
            del kwargs['hammer_timeouts']

        for key in kwargs:
            if key not in self.config.keys():
                raise error.GrabMisuseError('Unknown option: %s' % key)

        if 'url' in kwargs:
            if self.config.get('url'):
                kwargs['url'] = self.make_url_absolute(kwargs['url'])
        self.config.update(kwargs)

    def go(self, url, **kwargs):
        """
        Go to ``url``

        Args:
            :url: could be absolute or relative. If relative then t will be
            appended to the absolute URL of previous request.
        """

        return self.request(url=url, **kwargs)

    def download(self, url, location, **kwargs):
        """
        Fetch document located at ``url`` and save to to ``location``.
        """

        doc = self.go(url, **kwargs)
        with open(location, 'wb') as out:
            out.write(doc.body)
        return len(doc.body)

    def prepare_request(self, **kwargs):
        """
        Configure all things to make real network request.
        This method is called before doing real request via
        transport extension.
        """

        self.reset()
        self.request_counter = next(REQUEST_COUNTER)
        if kwargs:
            self.setup(**kwargs)
        if self.proxylist.size() and self.config['proxy_auto_change']:
            self.change_proxy()
        self.request_method = self.detect_request_method()
        self.transport.process_config(self)

    def log_request(self, extra=''):
        """
        Send request details to logging system.
        """

        thread_name = threading.currentThread().getName().lower()
        if thread_name == 'mainthread':
            thread_name = ''
        else:
            thread_name = '-%s' % thread_name

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
        logger_network.debug('[%02d%s] %s%s %s%s',
                             self.request_counter, thread_name,
                             extra, self.request_method or 'GET',
                             self.config['url'], proxy_info)

    def request(self, **kwargs):
        """
        Perform network request.

        You can specify grab settings in ``**kwargs``.
        Any keyword argument will be passed to ``self.config``.

        Returns: ``Document`` objects.
        """


        self.prepare_request(**kwargs)
        refresh_count = 0

        while True:
            self.log_request()

            try:
                self.transport.request()
            except error.GrabError:
                self.reset_temporary_options()
                self.save_failed_dump()
                raise
            else:
                doc = self.process_request_result()

                if self.config['follow_location']:
                    if doc.code in (301, 302, 303, 307, 308):
                        if doc.headers.get('Location'):
                            refresh_count += 1
                            if refresh_count > self.config['redirect_limit']:
                                raise error.GrabTooManyRedirectsError()
                            else:
                                url = doc.headers.get('Location')
                                self.prepare_request(
                                    url=self.make_url_absolute(url),
                                    referer=None)
                                continue

                if self.config['follow_refresh']:
                    refresh_url = self.doc.get_meta_refresh_url()
                    if refresh_url is not None:
                        refresh_count += 1
                        if refresh_count > self.config['redirect_limit']:
                            raise error.GrabTooManyRedirectsError()
                        else:
                            self.prepare_request(
                                url=self.make_url_absolute(refresh_url),
                                referer=None)
                            continue
                return doc

    def process_request_result(self, prepare_response_func=None):
        """
        Process result of real request performed via transport extension.
        """

        now = datetime.utcnow()
        # TODO: move into separate method
        if self.config['debug_post']:
            post = self.config['post'] or self.config['multipart_post']
            if isinstance(post, dict):
                post = list(post.items())
            if post:
                if isinstance(post, six.string_types):
                    post = post[:self.config['debug_post_limit']] + '...'
                else:
                    items = normalize_http_values(post, charset='utf-8')
                    new_items = []
                    for key, value in items:
                        if len(value) > self.config['debug_post_limit']:
                            value = value[
                                :self.config['debug_post_limit']] + '...'
                        else:
                            value = value
                        new_items.append((key, value))
                    post = '\n'.join('%-25s: %s' % x for x in new_items)
            if post:
                logger_network.debug('[%02d] POST request:\n%s\n'
                                     % (self.request_counter, post))

        # It's important to delete old POST data after request is performed.
        # If POST data is not cleared then next request will try to use them
        # again!
        self.reset_temporary_options()

        if prepare_response_func:
            self.doc = prepare_response_func(self.transport, self)
        else:
            self.doc = self.transport.prepare_response(self)

        # Workaround
        if self.doc.grab is None:
            self.doc.grab = weakref.proxy(self)

        if self.config['reuse_cookies']:
            self.cookies.update(self.doc.cookies)

        self.doc.timestamp = now

        self.config['charset'] = self.doc.charset

        if self.config['log_file']:
            with open(self.config['log_file'], 'wb') as out:
                out.write(self.doc.body)

        if self.config['cookiefile']:
            self.cookies.save_to_file(self.config['cookiefile'])

        if self.config['reuse_referer']:
            self.config['referer'] = self.doc.url

        self.copy_request_data()

        # Should be called after `copy_request_data`
        if self.config['log_dir']:
            self.save_dumps()

        return self.doc

    def reset_temporary_options(self):
        self.config['post'] = None
        self.config['multipart_post'] = None
        self.config['method'] = None
        self.config['body_storage_filename'] = None

    def save_failed_dump(self):
        """
        Save dump of failed request for debugging.

        This method is called then fatal network exception is raised.
        The saved dump could be used for debugging the reason of the failure.
        """

        # This is very untested feature, so
        # I put it inside try/except to not break
        # live spiders
        try:
            if self.transport_param == 'urllib3':
                # TODO: fix exceptions
                pass
            else:
                self.doc = self.transport.prepare_response(self)
                self.copy_request_data()
                if self.config['log_dir']:
                    self.save_dumps()
        except Exception as ex:
            logger.error('', exc_info=ex)

    def copy_request_data(self):
        # TODO: Maybe request object?
        self.request_head = self.transport.request_head
        self.request_body = self.transport.request_body
        #self.request_log = self.transport.request_log

    def setup_document(self, content, **kwargs):
        """
        Setup `response` object without real network requests.

        Useful for testing and debuging.

        All ``**kwargs`` will be passed to `Document` constructor.
        """

        self.reset()
        if isinstance(content, six.text_type):
            raise error.GrabMisuseError('Method `setup_document` accepts only '
                                        'byte string in `content` argument.')

        # Configure Document instance
        doc = Document(grab=self)
        doc.body = content
        doc.status = ''
        doc.head = b'HTTP/1.1 200 OK\r\n\r\n'
        doc.parse(charset=kwargs.get('document_charset'))
        doc.code = 200
        doc.total_time = 0
        doc.connect_time = 0
        doc.name_lookup_time = 0
        doc.url = ''

        for key, value in kwargs.items():
            setattr(doc, key, value)

        self.doc = doc

    def change_proxy(self):
        """
        Set random proxy from proxylist.
        """

        if self.proxylist.size():
            proxy = self.proxylist.get_random_proxy()
            self.setup(proxy=proxy.get_address(),
                       proxy_userpwd=proxy.get_userpwd(),
                       proxy_type=proxy.proxy_type)
        else:
            logger.debug('Proxy list is empty')

    def use_next_proxy(self):
        """
        Set next proxy from proxylist.
        """

        if self.proxylist.size():
            proxy = self.proxylist.get_next_proxy()
            self.setup(proxy=proxy.get_address(),
                       proxy_userpwd=proxy.get_userpwd(),
                       proxy_type=proxy.proxy_type)
        else:
            logger.debug('Proxy list is empty')

    """
    Private methods
    """

    def common_headers(self):
        """
        Build headers which sends typical browser.
        """

        return {
            'Accept': 'text/xml,application/xml,application/xhtml+xml'
                      ',text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.%d'
                      % randint(2, 5),
            'Accept-Language': 'en-us,en;q=0.%d' % (randint(5, 9)),
            'Accept-Charset': 'utf-8,windows-1251;q=0.7,*;q=0.%d'
                              % randint(5, 7),
            'Keep-Alive': '300',
        }

    def save_dumps(self):
        thread_name = threading.currentThread().getName().lower()
        if thread_name == 'mainthread':
            thread_name = ''
        else:
            thread_name = '-%s' % thread_name
        file_name = os.path.join(self.config['log_dir'], '%02d%s.log' % (
            self.request_counter, thread_name))
        with open(file_name, 'wb') as out:
            out.write(b'Request headers:\n')
            out.write(self.request_head)
            out.write(b'\n')
            out.write(b'Request body:\n')
            out.write(self.request_body)
            out.write(b'\n\n')
            out.write(b'Response headers:\n')
            out.write(self.doc.head)

        file_extension = 'html'
        file_name = os.path.join(self.config['log_dir'], '%02d%s.%s' % (
            self.request_counter, thread_name, file_extension))
        self.doc.save(file_name)

    def make_url_absolute(self, url, resolve_base=False):
        """
        Make url absolute using previous request url as base url.
        """

        if self.config['url']:
            if resolve_base:
                ubody = self.doc.unicode_body()
                base_url = find_base_url(ubody)
                if base_url:
                    return urljoin(base_url, url)
            return urljoin(self.config['url'], url)
        else:
            return url

    def detect_request_method(self):
        """
        Analyze request config and find which
        request method will be used.

        Returns request method in upper case

        This method needs simetime when `process_config` method
        was not called yet.
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
        self.cookies.clear()

    def setup_with_proxyline(self, line, proxy_type='http'):
        # TODO: remove from base class
        # maybe to proxylist?
        host, port, user, pwd = parse_proxy_line(line)
        server_port = '%s:%s' % (host, port)
        self.setup(proxy=server_port, proxy_type=proxy_type)
        if user:
            userpwd = '%s:%s' % (user, pwd)
            self.setup(proxy_userpwd=userpwd)

    def __getstate__(self):
        """
        Reset cached lxml objects which could not be pickled.
        """
        state = {}
        for cls in type(self).mro():
            cls_slots = getattr(cls, '__slots__', ())
            for slot in cls_slots:
                if slot != '__weakref__':
                    if hasattr(self, slot):
                        state[slot] = getattr(self, slot)

        if state['_doc']:
            state['_doc'].grab = weakref.proxy(self)

        return state

    def __setstate__(self, state):
        for slot, value in state.items():
            setattr(self, slot, value)

    @property
    def request_headers(self):
        """
        Temporary hack till the time I'll understand
        where to store request details.
        """

        try:
            first_head = self.request_head.decode('utf-8').split('\r\n\r\n')[0]
            lines = first_head.split('\r\n')
            lines = [x for x in lines if ':' in x]
            headers = email.message_from_string('\n'.join(lines))
            return headers
        except Exception as ex:
            logger.error('Could not parse request headers', exc_info=ex)
            return {}

    def dump(self):
        """
        Shortcut for real-time debugging.
        """
        self.doc.save('/tmp/x.html')


# For backward compatibility
# WTF???
BaseGrab = Grab
