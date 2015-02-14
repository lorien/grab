"""
Module contents:
* `Proxy` class represent single proxy server
* `ProxyList` class is interface to work with list of proxy servers
* `LocalFileSource` contains logic to load list of proxies from local file
* `RemoteFileSource contains logic to load list of proxies from remote document.
"""
import re
import itertools
import time
import logging
import random

from grab.error import GrabError, GrabNetworkError
from grab.util.py2old_support import *
from grab.util.py3k_support import *

RE_SIMPLE_PROXY = re.compile(r'^([^:]+):([^:]+)$')
RE_AUTH_PROXY = re.compile(r'^([^:]+):([^:]+):([^:]+):([^:]+)$')
logger = logging.getLogger('grab.proxy')


def parse_proxy_line(line):
    """
    Extract proxy details from the text line.

    The text line could be in one of the following formats:
    * host:port
    * host:port:username:password
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


class Proxy(object):
    """
    Represents single proxy server.
    """

    def __init__(self, server, port, username=None, password=None,
                 proxy_type='http'):
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.proxy_type = proxy_type

    @property
    def address(self):
        return '%s:%s' % (self.server, self.port)

    @property
    def userpwd(self):
        return '%s:%s' % (self.username, self.password)

    def __cmp__(self, obj):
        if (self.server == obj.server and self.port == obj.port and
                self.username == obj.username and self.password == obj.password and
                self.proxy_type == obj.proxy_type):
            return 0
        else:
            return 1


def parse_proxy_data(data, data_format='text', proxy_type='http'):
    """
    Yield `Proxy` objects found in the given `data`.
    """
    if data_format == 'text':
        for line in data.splitlines():
            if not PY3K and isinstance(line, unicode):
                line = line.encode('utf-8')
            line = line.strip().replace(' ', '')
            if line and not line.startswith('#'):
                try:
                    host, port, user, pwd = parse_proxy_line(line)
                except GrabError as ex:
                    logger.error('Invalid proxy line: %s' % line)
                else:
                    yield Proxy(host, port, user, pwd, proxy_type)
    else:
        raise GrabError('Unknown proxy data format: %s' % data_format)


class ProxySource(object):
    """
    Generic proxy source interface.
    """

    def load(self):
        return list(parse_proxy_data(
            self.load_data(),
            data_format=self.data_format,
            proxy_type=self.proxy_type,
        ))


class LocalFileSource(ProxySource):
    """
    Proxy source that loads data from the file in local file system.
    """

    def __init__(self, location, safe_load=False, data_format='text',
                 proxy_type='http'):
        self.location = location
        self.data_format = data_format
        self.safe_load = False
        self.proxy_type = proxy_type

    def load_data(self):
        try:
            return open(self.location).read()
        except Exception as ex:
            if self.safe_load:
                logger.error('', format_exc=ex)
                return ''
            else:
                raise


class RemoteFileSource(ProxySource):
    """
    Proxy source that loads data from the remote document.
    """

    def __init__(self, url, safe_load=False, data_format='text',
                 proxy_type='http'):
        self.url = url
        self.data_format = data_format
        self.safe_load = False
        self.proxy_type = proxy_type

    def load_data(self):
        from grab import Grab

        g = Grab()
        try:
            g.go(self.url)
        except GrabNetworkError as ex:
            if self.safe_load:
                logger.error('', format_exc=ex)
                return ''
            else:
                raise
        else:
            return g.response.body

# List of aliases that is used in `ProxyList::set_source` function
SOURCE_TYPE_ALIAS = {
    'file': LocalFileSource,
    'url': RemoteFileSource,
}


class ProxyList(object):
    """
    Main class to work with proxy list.
    """

    def __init__(self, **kwargs):
        """
        Args:
            accumulate_updates: if it is True, then update existing proxy list
            with new proxy list when do reloading
        """
        self.source = None
        self.proxy_list = []
        self.iterator_index = 0
        self.setup(**kwargs)

    def setup(self, accumulate_updates=False, reload_time=600):
        self.accumulate_updates = accumulate_updates
        self.reload_time = reload_time

    def set_source(self, source_type='file', proxy_type='http', **kwargs):
        """
        Configure proxy list source and load proxies from that source.
        """

        if source_type in SOURCE_TYPE_ALIAS:
            source_cls = SOURCE_TYPE_ALIAS[source_type]
            self.source = source_cls(proxy_type=proxy_type, **kwargs)
            self.reload(force=True)
        else:
            raise GrabError('Unknown source type: %s' % source_type)

    def reload(self, force=False):
        """
        Reload proxies from the configured proxy list source.
        """

        now = time.time()
        if force or now - self.load_timestamp > self.reload_time:
            self.load_timestamp = now
            if not self.accumulate_updates:
                self.proxy_list = self.source.load()
                self.iterator_index = 0
            else:
                new_list = self.source.load()
                for item in new_list:
                    if not item in self.proxy_list:
                        self.proxy_list.append(item)

            self.proxy_list_iter = itertools.cycle(self.proxy_list)

    def get_random_proxy(self):
        """
        Return random server from the list
        """

        self.reload()
        self.iterator_index = random.randint(0, len(self.proxy_list) - 1)
        return self.proxy_list[self.iterator_index]

    def get_next_proxy(self):
        """
        Return next server in the list.
        """

        self.reload()
        if (self.iterator_index + 1) > len(self.proxy_list):
            self.iterator_index = 0
        proxy = self.proxy_list[self.iterator_index]
        self.iterator_index += 1
        return proxy

    def is_empty(self):
        """
        Check if the proxy list is empty.
        """

        return len(self.proxy_list) == 0
