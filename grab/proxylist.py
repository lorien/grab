from __future__ import absolute_import
import re
import itertools
import logging
from random import randint
import six
from collections import namedtuple

from grab.error import GrabError, GrabNetworkError

RE_SIMPLE_PROXY = re.compile(r'^([^:]+):([^:]+)$')
RE_AUTH_PROXY = re.compile(r'^([^:]+):([^:]+):([^:]+):([^:]+)$')
PROXY_FIELDS = ('host', 'port', 'username', 'password', 'proxy_type')
logger = logging.getLogger('grab.proxylist')


class Proxy(namedtuple('Proxy', PROXY_FIELDS)):
    def get_address(self):
        return '%s:%s' % (self.host, self.port)

    def get_userpwd(self):
        if self.username:
            return '%s:%s' % (self.username, self.password or '')


class InvalidProxyLine(GrabError):
    pass


def parse_proxy_line(line):
    """
    Parse proxy details from the raw text line.

    The text line could be in one of the following formats:
    * host:port
    * host:port:username:password
    """

    line = line.strip()
    match = RE_SIMPLE_PROXY.search(line)
    if match:
        return match.group(1), match.group(2), None, None

    match = RE_AUTH_PROXY.search(line)
    if match:
        host, port, user, pwd = match.groups()
        return host, port, user, pwd

    raise InvalidProxyLine('Invalid proxy line: %s' % line)


def parse_raw_list_data(data, proxy_type='http', proxy_userpwd=None):
    "Iterate over proxy servers found in the raw data"
    if not isinstance(data, six.text_type):
        data = data.decode('utf-8')
    for orig_line in data.splitlines():
        line = orig_line.strip().replace(' ', '')
        if line and not line.startswith('#'):
            try:
                host, port, username, password = parse_proxy_line(line)
            except InvalidProxyLine as ex:
                logger.error(ex)
            else:
                if username is None and proxy_userpwd is not None:
                    username, password = proxy_userpwd.split(':')
                yield Proxy(host, port, username, password, proxy_type)


class BaseProxySource(object):
    def __init__(self, proxy_type='http', proxy_userpwd=None, **kwargs):
        kwargs['proxy_type'] = proxy_type
        kwargs['proxy_userpwd'] = proxy_userpwd
        self.config = kwargs

    def load_raw_data(self):
        raise NotImplementedError

    def load(self):
        data = self.load_raw_data()
        return list(parse_raw_list_data(
            data,
            proxy_type=self.config['proxy_type'],
            proxy_userpwd=self.config['proxy_userpwd']))


class FileProxySource(BaseProxySource):
    "Proxy source that loads list from the file"
    def __init__(self, path, **kwargs):
        self.path = path
        super(FileProxySource, self).__init__(**kwargs)

    def load_raw_data(self):
        return open(self.path).read()


class WebProxySource(BaseProxySource):
    "Proxy source that loads list from web resource"
    def __init__(self, url, **kwargs):
        self.url = url
        super(WebProxySource, self).__init__(**kwargs)

    def load_raw_data(self):
        from grab import Grab
        limit = 3
        for count in range(limit):
            try:
                return Grab().go(url=self.url).unicode_body()
            except GrabNetworkError:
                if count >= (limit - 1):
                    raise


class ListProxySource(BaseProxySource):
    """That proxy source that loads list from
    python list of strings"""
    def __init__(self, items, **kwargs):
        self.items = items
        super(ListProxySource, self).__init__(**kwargs)

    def load_raw_data(self):
        return '\n'.join(self.items)


class ProxyList(object):
    """
    Class to work with proxy list.
    """

    def __init__(self, source=None):
        self._source = source
        self._list = []
        self._list_iter = None

    def set_source(self, source):
        "Set the proxy source and use it to load proxy list"
        self._source = source
        self.load()

    def load_file(self, path, **kwargs):
        "Load proxy list from file"
        self.set_source(FileProxySource(path, **kwargs))

    def load_url(self, url, **kwargs):
        "Load proxy list from web document"
        self.set_source(WebProxySource(url, **kwargs))

    def load_list(self, items, **kwargs):
        "Load proxy list from python list"
        self.set_source(ListProxySource(items, **kwargs))

    def load(self):
        "Load proxy list from configured proxy source"
        self._list = self._source.load()
        self._list_iter = itertools.cycle(self._list)

    def get_random_proxy(self):
        "Return random proxy"
        idx = randint(0, len(self._list) - 1)
        return self._list[idx]

    def get_next_proxy(self):
        "Return next proxy"
        return next(self._list_iter)

    def size(self):
        "Return number of proxies in the list"
        return len(self._list)

    def __iter__(self):
        return iter(self._list)

    def __len__(self):
        return len(self._list)

    def __getitem__(self, key):
        return self._list[key]
