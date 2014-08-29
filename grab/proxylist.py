"""
THIS IS DEPRECATED MODULE.
USE grab.proxy MODULE INSTEAD.

Module to work with proxy list.

Usage:

    pl = ProxyList('var/proxy.txt', 'socks5')
    g = Grab()
    server, userpwd = pl.get_random()
    g.setup(proxy=server, userpwd=userpwd)

Or you can do even simpler:

    g = Grab()
    g.setup(proxylist=('var/proxy.txt', 'socks5'))
    g.change_proxy()

"""
import itertools
from random import choice
import re
import logging
from copy import deepcopy
import time
import logging
try:
    from urllib2 import urlopen, URLError, HTTPError
except ImportError:
    from urllib.request import urlopen
    from urllib.error import URLError, HTTPError

from grab.error import GrabError, GrabNetworkError, GrabMisuseError
from grab.util.py2old_support import *
from grab.util.py3k_support import *

READ_TIMEOUT = 60 * 10
RE_SIMPLE_PROXY = re.compile(r'^([^:]+):([^:]+)$')
RE_AUTH_PROXY = re.compile(r'^([^:]+):([^:]+):([^:]+):([^:]+)$')
logger = logging.getLogger('grab.proxylist')


def parse_proxyline(line):
    """
    Extract proxy details from the text line.
    """

    match = RE_SIMPLE_PROXY.search(line)
    if match:
        host, port = match.groups()
        return host, port, None, None
    else:
        match = RE_AUTH_PROXY.search(line)
        if match:
            host, port, user, pwd = match.groups()
            return host, port, user, pwd
    raise GrabError('Invalid proxy line: %s' % line)


class ProxySource(object):

    def __init__(self, source, read_timeout=READ_TIMEOUT, proxy_type='http'):
        self.source = source
        self.read_timeout = read_timeout
        self.proxy_type = proxy_type
        self.read_time = None

    def parse_lines(self, proxies):
        """
        Parse each line from proxies list step by step.
        Returns tuple with server (host:port) and user_pwd (user:password)
        :param proxies: list which contains proxy servers
        """

        for proxy in proxies:
            if not PY3K and isinstance(proxy, unicode):
                # Convert to string (py2.x)
                proxy = proxy.encode('utf-8')
            proxy = proxy.strip().replace(' ', '')
            if proxy:
                host, port, user, pwd = parse_proxyline(proxy)
                server = '%s:%s' % (host, port)
                user_pwd = None
                if user:
                    user_pwd = '%s:%s' % (user, pwd)
                yield server, user_pwd

    def get_server_list(self, proxylist):
        if not PY3K and isinstance(proxylist, unicode):
            # Convert to string (py2.x)
            proxylist = proxylist.encode('utf-8')
        if isinstance(proxylist, str):
            proxylist = proxylist.split()
        servers = []
        for server, user_pwd in self.parse_lines(proxylist):
            servers.append((server, user_pwd, self.proxy_type))
        return servers

    def load(self):
        pass

    def reload(self):
        """
        Update proxy list.
        
        Re-read proxy file after each XX seconds.
        """
        
        if (self.read_time is None or
                (time.time() - self.read_time) > self.read_timeout):
            logger.debug('Reloading proxy list')
            self.load()
            return True
        else:
            return False


class TextFileSource(ProxySource):
    source_type = 'text_file'

    def load(self):
        """
        Load proxy list from specified source and validate loaded data.

        Each server could be in two forms:
        * simple: "server:port"
        * complex: "server:port:user:pwd"
        """

        with open(self.source) as src:
            lines = src.read().splitlines()

        self.read_time = time.time()
        self.server_list = self.get_server_list(lines)
        self.server_list_iterator = itertools.cycle(self.server_list)


class URLSource(ProxySource):
    source_type = 'url'

    def load(self):
        """
        Load proxy list from specified URL and validate loaded data.

        Each proxy server could be in two forms:
        * simple: "server:port"
        * complex: "server:port:user:pwd"
        """
        try:
            proxylist = urlopen(self.source).readlines()
        except (URLError, HTTPError):
            raise GrabNetworkError("Can't load proxies from URL (%s)"
                                   % self.source)

        self.read_time = time.time()
        self.server_list = self.get_server_list(proxylist)
        self.server_list_iterator = itertools.cycle(self.server_list)


class ListSource(ProxySource):
    source_type = 'list'

    def load(self):
        """
        Load proxies from given list.

        Each proxy server could be in two forms:
        * simple: "server:port"
        * complex: "server:port:user:pwd"
        """

        if not isinstance(self.source, list):
            raise GrabMisuseError("Given proxy list isn't a list type")
        self.server_list = self.get_server_list(self.source)
        self.server_list_iterator = itertools.cycle(self.server_list)

    def reload(self):
        pass


class StringSource(ProxySource):
    source_type = 'string'

    def load(self):
        """
        Load proxies from given string. String can be multiline.

        Each proxy server could be in two forms:
        * simple: "server:port"
        * complex: "server:port:user:pwd"
        """

        if not isinstance(self.source, (str, unicode)):
            raise GrabMisuseError("Given proxy list isn't a string or unicode "
                                  "type")
        self.server_list = self.get_server_list(self.source)
        self.server_list_iterator = itertools.cycle(self.server_list)

    def reload(self):
        pass


SOURCE_LIST = {
    'text_file': TextFileSource,
    'url': URLSource,
    'list': ListSource,
    'string': StringSource,
}


class ProxyList(object):
    """
    Class to work with proxy list which 
    is stored in the plain text file.
    """

    def __init__(self, source, source_type, proxy_type='http', **kwargs):
        """
        Create `ProxyList` object and load proxies from the specified source.

        You should specify type of source in second argument to let ProxyList
        instance know how to handle proxy source.

        :param source: source of the project (file name, string or some object)
        :param source_type: type of proxy source
        :param proxy_type: default type of proxy (if proxy source does not
        provide this information)
        :param **kwargs: any additional arguments goes to specific proxy load
        method
        """

        self.init_kwargs = deepcopy(kwargs)

        try:
            source_class = SOURCE_LIST[source_type]
        except AttributeError:
            raise GrabMisuseError('Unknown proxy source type: %s'
                                  % source_type)
        self.source = source_class(source, proxy_type=proxy_type, **kwargs)
        self.source.load()
        self.filter_config = {}
        self.geoip_resolver = None

    def filter_by_country(self, code, geoip_db_path):
        # geoip_db_path -yep, this is quick & crapy workaround
        self.filter_config['country'] = {'code': code.lower(),
                                         'geoip_db_path': geoip_db_path}
        self.apply_filter()

    def apply_filter(self):
        if self.filter_config.get('country'):
            geoip = self.get_geoip_resolver()
            new_list = []
            for row in self.source.server_list:
                server, userpwd, proxy_type = row
                host = server.split(':')[0]
                country = geoip.country_code_by_addr(host).lower()
                if country == self.filter_config['country']['code']:
                    new_list.append(row)
            self.source.server_list = row
            self.source.server_list_iterator = \
                itertools.cycle(self.source.server_list)

    def get_geoip_resolver(self):
        if self.geoip_resolver is None:
            import pygeoip
            self.geoip_resolver = \
                pygeoip.GeoIP(self.filter_config['country']['geoip_db_path'],
                              pygeoip.MEMORY_CACHE)
        return self.geoip_resolver

    def get_random(self):
        """
        Return random server from the list
        """

        if self.source.reload():
            self.apply_filter()
        return choice(self.source.server_list)

    def get_next(self):
        """
        Return next server in the list.
        """

        logger.debug('Changing proxy')
        if self.source.reload():
            self.apply_filter()
        return next(self.source.server_list_iterator)
