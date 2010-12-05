# -*- coding: utf-8 -*-
import logging
import os
import urllib
from random import randint, choice
from copy import copy
import threading
from urlparse import urljoin
from copy import deepcopy

from html import make_unicode, find_refresh_url
import user_agent

__all__ = ['Grab', 'GrabError', 'DataNotFound']

DEFAULT_EXTENSIONS = ['grab.ext.pycurl', 'grab.ext.lxml', 'grab.ext.lxml_form']
logger = logging.getLogger('grab')

class GrabError(IOError):
    pass

class DataNotFound(Exception):
    pass

class ImproperlyConfigured(Exception):
    pass

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
        debug_post = False,
        encoding = 'gzip',
    )

class Response(object):
    """
    HTTP Response.
    """

    def __init__(self):
        self.status = None
        self.code = None
        self.head = None
        self.body = None
        self.headers =None
        self.time = None
        self.url = None
        self.cookies = None

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
                        logging.error('Invalid header line: %s' % line, exc_info=ex)


class Grab(object):
    # Shortcut to grab.GrabError
    Error = GrabError

    # This counter will used in enumerating network queries.
    # Its values will be displayed in logging messages and also used
    # in names of dumps
    request_counter = -1

    # Attributes which should be processed when clone
    # of Grab instance is creating
    clonable_attributes = ['request_headers', 'request_counter']

    # Info about loaded extensions
    extensions = []
    transport_extension = None

    def __init__(self, extensions=DEFAULT_EXTENSIONS, extra_extensions=None, **kwargs):
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

    def trigger_extensions(self, event):
        for ext in self.extensions:
            try:
                getattr(ext, 'extra_%s' % event)(self)
            except AttributeError:
                pass

    def process_config(self):
        raise ImproperlyConfigured('process_config method should be redefined by transport extension')

    def extract_cookies(self):
           raise ImproperlyConfigured('extract_cookies method should be redefined by transport extension')

    def prepare_response(self):
           raise ImproperlyConfigured('prepare_response method should be redefined by transport extension')


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
        self.trigger_extensions('reset')

    def clone(self):
        """
        Create clone of Grab instance.

        Try to save its state: cookies, referer, response data
        """

        g = Grab()
        g.config = deepcopy(self.config)
        # Important for pycurl transport
        # By default pycurl use own implementation 
        # of cookies. So when we create new Grab instance
        # and hence new pycurl instance and configure it
        # with ``config`` of old Grab instance then new
        # pycurl instance does not 
        # anything about cookies (because info about them
        # does not contains in config - it contains in some
        # internal structure of old pycurl instance.
        # What is why we explicitly configure cookies
        # of new pycurl instance - we know where to get them
        # cookies are always processed in Response instance
        # Yeh... newer wrote so long comment!
        g.setup(cookies=self.response.cookies)
        g.response = deepcopy(self.response)
        for key in self.clonable_attributes:
            setattr(g, key, getattr(self, key))
        return g


    def setup(self, **kwargs):
        """
        Change configuration.
        """

        if 'url' in kwargs:
            if self.config.get('url'):
                url = urljoin(self.config['url'], kwargs['url'])
                kwargs['url'] = url
        self.config.update(kwargs)

    def go(self, url):
        """
        Go to ``url``

        Args:
            :url: could be absolute or relative. If relative then will be appended to the
                absolute URL of previous request.
        """

        return self.request(url=url)


    def request(self, **kwargs):
        # Reset the state setted by prevous request
        self.reset()
        if kwargs:
            self.setup(**kwargs)
        self.process_config()

        self.transport_extension.request(self)
        if self.config['debug_post']:
            if self.config['post']:
                items = sorted(self.config['post'].items(), key=lambda x: x[0])
                rows = '\n'.join('%-25s: %s' % x for x in items)
                logging.debug('POST request:\n%s\n' % rows)

        # It's vital to delete old POST data after request is performed.
        # If POST data remains when next request will try to use them again!
        # This is not what typical user waits.
        self.old_config = deepcopy(self.config) 
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
            url = find_refresh_url(self.response.body)
            if url:
                return self.request(url=url)

        return self.response

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
            return anchor.search(self.response.body) or None
        else:
            if isinstance(anchor, unicode):
                anchor = anchor.encode(self.config['charset'])
            return anchor if self.response.body.find(anchor) > -1 else None

    def assert_pattern(self, anchor):
        """
        Search for string or regexp.
        
        If nothing found raise DataNotFound exception.
        """

        if not self.search(anchor):
            raise DataNotFound(u'Could not found pattern: %s' % anchor)

    def reload(self):
        """
        Load current url again.
        """

        self.go('')

    def repeat_request(self):
        self.config = self.old_config
        self.request()

    # TODO: probably should be in Response class
    # or in new extension which also should include search and assert_pattern methods
    @property
    def unicode_body(self):
        if not self._unicode_body:
            self._unicode_body = make_unicode(self.response.body, self.config['guess_encodings'])
        return self._unicode_body
