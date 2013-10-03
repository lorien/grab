"""
This modules contains classes that helps to work
with lists of proxy servers.
"""
import re
import itertools
import time

from .error import GrabError, GrabNetworkError
from .util.py2old_support import *
from .util.py3k_support import *

RE_SIMPLE_PROXY = re.compile(r'^([^:]+):([^:]+)$')
RE_AUTH_PROXY = re.compile(r'^([^:]+):([^:]+):([^:]+):([^:]+)$')


def parse_proxy_line(line):
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


class Proxy(object):
    def __init__(self, server, port, user=None, password=None):
        self.server = server
        self.port = port
        self.user = user
        self.password = password


def parse_proxy_data(data, data_format='text'):
    if data_format == 'text':
        for line in data.splitlines():
            if not PY3K and isinstance(line, unicode):
                line = line.encode('utf-8')
            line = line.strip().replace(' ', '')
            if line and not line.startswith('#'):
                try:
                    host, port, user, pwd = parse_proxy_line(line)
                except GrabError as ex:
                    logging.error('Invalid proxy line: %s' % line)
                else:
                    yield Proxy(host, port, user, pwd)
    else:
        raise GrabError('Unknown proxy data format: %s' % data_format)


class ProxySource(object):
    def load(self):
        return list(parse_proxy_data(self.load_data(), self.data_format))


class LocalFileSource(ProxySource):
    def __init__(self, location, safe_load=False, data_format='text'):
        self.location = location
        self.data_format = data_format
        self.safe_load = False

    def load_data(self):
        try:
            return open(self.location).read()
        except Exception as ex:
            if self.safe_load:
                logging.error('', format_exc=ex)
                return ''
            else:
                raise


class RemoteFileSource(ProxySource):
    def __init__(self, url, safe_load=False, data_format='text'):
        self.url = url
        self.data_format = data_format
        self.safe_load = False

    def load_data(self):
        from grab import Grab

        g = Grab()
        try:
            g.go(self.url)
        except GrabNetworkError as ex:
            if self.safe_load:
                logging.error('', format_exc=ex)
                return ''
            else:
                raise
        else:
            return g.response.body


SOURCE_TYPE_ALIAS = {
    'file': LocalFileSource,
    'url': RemoteFileSource,
}


class ProxyList(object):
    def __init__(self):
        self.proxy_list = []
        self.source = None
        self.proxy_list_iter = None

    def set_source(self, source_type='file', reload_time=600, **kwargs):
        self.reload_time = reload_time
        if source_type in SOURCE_TYPE_ALIAS:
            source_cls = SOURCE_TYPE_ALIAS[source_type]
            self.source = source_cls(**kwargs)
            self.reload(force=True)
        else:
            raise GrabError('Unknown source type: %s' % source_type)

    def reload(self, force=False):
        now = time.time()
        if force or now - self.load_timestamp > self.reload_time:
            self.load_timestamp = now
            self.proxy_list = self.source.load()
            self.proxy_list_iter = itertools.cycle(self.proxy_list)

    def get_random_proxy(self):
        """
        Return random server from the list
        """

        self.reload()
        return choice(self.proxy_list)

    def get_next(self):
        """
        Return next server in the list.
        """

        self.reload()
        return next(self.proxy_list_iter)
