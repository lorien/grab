# -*- coding: utf-8 -*-
# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
"""
Exceptions:

Exception
-> GrabError
---> GrabNetworkError <- IOError 
---> DataNotFound
"""

import logging
import os
import urllib
from random import randint, choice
from copy import copy
import threading
from urlparse import urljoin
from copy import deepcopy
import time
import re

from html import make_unicode, find_refresh_url
import user_agent
from response import Response

__all__ = ('Grab', 'GrabError', 'DataNotFound', 'GrabNetworkError', 'GrabMisuseError',
           'UploadContent', 'UploadFile')

GLOBAL_STATE = {'request_counter': 0}
DEFAULT_EXTENSIONS = ['grab.ext.pycurl', 'grab.ext.lxml', 'grab.ext.lxml_form',
                      'grab.ext.django', 'grab.ext.text']
logger = logging.getLogger('grab')

class GrabError(Exception):
    """
    All custom Grab exception should be children of that class.
    """

class GrabNetworkError(IOError, GrabError):
    """
    Wrapper about pycurl error.
    """


class DataNotFound(IndexError, GrabError):
    """
    Indictes that required data is not found.
    """


class GrabMisuseError(GrabError):
    """
    Indicates incorrect usage of grab API.
    """


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
        charset = 'utf-8',
        user_agent = choice(user_agent.variants),
        reuse_cookies = True,
        reuse_referer = True,
        cookies = {},
        cookiefile = None,
        referer = None,
        guess_encodings = ['windows-1251', 'koi8-r', 'utf-8'],
        log_file = None,
        log_dir = False,
        follow_refresh = False,
        nohead = False,
        nobody = False,
        debug = False,
        debug_post = False,
        encoding = 'gzip',
        userpwd = None,
        # Timeouts
        timeout = 15,
        connect_timeout = 10,
        hammer_mode = False,
        hammer_timeouts = ((2, 5), (5, 10), (10, 20), (15, 30)),
        lowercased_tree = False,
    )

VALID_CONFIG_KEYS = default_config().keys()



class Grab(object):
    # Shortcut to grab.GrabError
    Error = GrabError

    # Attributes which should be processed when clone
    # of Grab instance is creating
    clonable_attributes = ['request_headers', 'request_head', 'request_log', 'request_body']

    # Info about loaded extensions
    extensions = []
    transport_extension = None

    """
    Public methods
    """

    def __init__(self, extensions=DEFAULT_EXTENSIONS, extra_extensions=None, **kwargs):
        """
        By default grab instance is initiated with some extensions. You can
        override list of extension in ``extensions`` attribute or specify additional
        extensions in ``extra_extensions`` attribute. All other named arguments will
        be treated as settings.
        """

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
        self.trigger_extensions('init')
        self.reset()
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

        g = Grab()
        g.config = deepcopy(self.config)
        # Important for pycurl transport
        # By default pycurl use own implementation 
        # of cookies. So when we create new Grab instance
        # and hence new pycurl instance and configure it
        # with ``config`` of old Grab instance then new
        # pycurl instance does not know
        # anything about cookies (because info about them
        # does not contains in config - it contains in some
        # internal structure of old pycurl instance).
        # What is why we explicitly configure cookies
        # of new pycurl instance - we know where to get them from:
        # cookies are always processed in Response instance
        cookies = self.config['cookies']
        cookies.update(self.response.cookies)
        g.setup(cookies=cookies)
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
            if not key in VALID_CONFIG_KEYS:
                raise GrabMisuseError('Unknown option: %s' % key)

        if 'url' in kwargs:
            if self.config.get('url'):
                url = urljoin(self.config['url'], kwargs['url'])
                kwargs['url'] = url
        self.config.update(kwargs)

    def go(self, url, **kwargs):
        """
        Go to ``url``

        Args:
            :url: could be absolute or relative. If relative then t will be appended to the
                absolute URL of previous request.
        """

        return self.request(url=url, **kwargs)

    def request(self, **kwargs):
        """
        Perform network request.

        You can specify grab settings in ``**kwargs``.

        Any keywrod argument will be passed to ``self.config`` except:

        * controller - it should be callable which will be called at the end
        of request. You can control the results of request with controller 
        function and, for example, do the same request again in case of some error.

        Returns: ``Response`` objects.
        """

        controller = kwargs.pop('controller', None)

        if self.config['hammer_mode']:
            hammer_timeouts = list(self.config['hammer_timeouts'])
            connect_timeout, total_timeout = hammer_timeouts.pop(0)
            self.setup(connect_timeout=connect_timeout, timeout=total_timeout)

        while True:
            try:
                # Reset the state setted by prevous request
                self.reset()
                self.increase_request_counter()
                if kwargs:
                    self.setup(**kwargs)
                self.process_config()

                self.transport_extension.request(self)
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

        if self.config['debug_post']:
            post = self.config['post'] or self.config['multipart_post']
            if isinstance(post, dict):
                post = post.items()
            if post:
                post = self.normalize_tuples(post)
                items = sorted(post, key=lambda x: x[0])
                items = [(x[0], str(x[1])[:150]) for x in items]
                rows = '\n'.join('%-25s: %s' % x for x in items)
                logger.debug('POST request:\n%s\n' % rows)

        # It's important to delete old POST data after request is performed.
        # If POST data remains when next request will try to use them again!
        # This is not what typical user waits.
        self.old_config = deepcopy(self.config) 
        self.config['post'] = None
        self.config['multipart_post'] = None
        self.config['method'] = None

        self.prepare_response()

        # TODO: raise GrabWarning if self.config['http_warnings']
        #if 400 <= self.response_code:
            #raise IOError('Response code is %s: ' % self.response_code)

        if self.config['log_file']:
            open(self.config['log_file'], 'w').write(self.response.body)

        self.save_dumps()

        if self.config['cookiefile']:
            self.dump_cookies(self.config['cookiefile'])

        if self.config['reuse_referer']:
            self.config['referer'] = self.response.url

        # TODO: check max redirect count
        if self.config['follow_refresh']:
            url = find_refresh_url(self.response.body)
            if url:
                return self.request(url=url)

        if controller:
            controller(self)

        return self.response

    def repeat_request(self):
        """
        Make the same network request again.

        All cookies, POST data, headers will be sent again.
        """

        self.config = deepcopy(self.old_config)
        self.request()

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

    """
    Private methods
    """

    @property
    def request_counter(self):
        # This counter will used in enumerating network queries.
        # Its value will be displayed in logging messages and also used
        # in names of dumps
        # I use mutable module variable to allow different
        # instances of Grab maintain single counter
        # This could be helpful in debuggin when your script
        # creates multiple Grab instances - in case of shared counter
        # grab instances do not overwrite dump logs
        return GLOBAL_STATE['request_counter']


    def trigger_extensions(self, event):
        for ext in self.extensions:
            try:
                getattr(ext, 'extra_%s' % event)(self)
            except AttributeError:
                pass

    def process_config(self):
        raise NotImplemented('process_config method should be redefined by transport extension')

    def extract_cookies(self):
       raise NotImplemented('extract_cookies method should be redefined by transport extension')

    def prepare_response(self):
       raise NotImplemented('prepare_response method should be redefined by transport extension')

    def load_extension(self, ext_class):
        for attr in ext_class.export_attributes:
            self.add_to_class(attr, ext_class.__dict__[attr])
        ext = ext_class()
        self.extensions.append(ext)
        if getattr(ext, 'transport', None):
            self.transport_extension = ext

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
            'Expect': '',
        }

    def increase_request_counter(self):
        GLOBAL_STATE['request_counter'] += 1

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

    def urlencode(self, items):
        """
        Smart urlencode which know how to process unicode strings and None values.
        """

        if isinstance(items, dict):
            items = items.items()
        return urllib.urlencode(self.normalize_tuples(items))

    # TODO: Change that stupid name
    def normalize_tuples(self, items):
        """
        Convert second value in each tuple into byte strings.

        That functions prepare data for passing into pycurl library.
        Pycurl can not handle unicode or None values.
        """

        def process(item):
            key, value = item
            if isinstance(value, (UploadContent, UploadFile)):
                value = value.field_tuple()
            elif isinstance(value, unicode):
                value = value.encode(self.response.charset)
            elif value is None:
                value = ''
            return key, value
        return map(process, items)

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


class UploadContent(str):
    def __new__(cls, value):
        obj = str.__new__(cls, 'xxx')
        obj.raw_value = value
        return obj

    def field_tuple(self):
        import pycurl
        return (pycurl.FORM_CONTENTS, self.raw_value)


class UploadFile(str):
    def __new__(cls, path):
        obj = str.__new__(cls, 'xxx')
        obj.path = path
        return obj

    def field_tuple(self):
        import pycurl
        return (pycurl.FORM_FILE, self.path)
