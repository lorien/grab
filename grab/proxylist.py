"""
Module to work with proxy list.

Usage:

    pl = ProxyList('var/proxy.txt', 'socks5')
    g = Grab()
    server, userpwd = pl.get_random()
    g.setup(proxy=server, userpwd=userpwd)

Or you can do even simplier:

    g = Grab()
    g.setup(proxylist=('var/proxy.txt', 'socks5'))
    g.change_proxy()

"""
import itertools
from random import choice
from datetime import datetime, timedelta
import re
import logging

from error import GrabError, GrabMisuseError

READ_TIMEOUT = 60 * 10
RE_SIMPLE_PROXY = re.compile(r'^([^:]+):([^:]+)$')
RE_AUTH_PROXY = re.compile(r'^([^:]+):([^:]+):([^:]+):([^:]+)$')

def parse_proxyline(line):
    """
    Extract proxy details from the text line.
    """

    line = line.strip()
    match = RE_SIMPLE_PROXY.search(line)
    if match:
        host, port = match.groups()
        return host, port, None, None
    else:
        match = RE_AUTH_PROXY.search(line)
        host, port, user, pwd = match.groups()
        if match:
            return host, port, user, pwd
    raise GrabError('Invalid proxy line: %s' % line)


class ProxyList(object):
    """
    Class to work with proxy list which 
    is stored in the plain text file.
    """

    def __init__(self, proxy_file=None, proxy_type='http', read_timeout=None,
                 server_list=None):
        """
        Create `ProxyList` object and load proxies from the specified source.

        You can specify source either with `proxy_file` or `server_list` options.

        Args:
            :param proxy_file: path to file which contains list of servers.
                Each server could be in two forms:
                * simple: "server:port"
                * complex: "server:port:user:pwd"
            :param server_list: list of servers. Each item should be a string
                of format described in description of `proxy_file` option.
            :param proxy_type: type of proxies. All proxies should be of the same
                type
            :param read_timeout: time after which the proxy list will be reloaded
                By deafult, it is 600 seconds.
        """

        if proxy_file is None and server_list is None:
            raise GrabMisuseError('ProxyList constructor: both proxy_file and'\
                                  ' server_list options are None')
        elif proxy_file is not None and server_list is not None:
            raise GrabMisuseError('ProxyList constructor: only one of proxy_file and'
                                  ' server_list options could be non-None')
        elif proxy_file is not None:
            self.proxy_file = proxy_file
            self.server_list = None
        else:
            self.proxy_file = None
            self.server_list = server_list
        self.proxy_type = proxy_type
        if read_timeout is None:
            self.read_timeout = READ_TIMEOUT
        else:
            self.read_timeout = read_timeout
        self.read_time = None
        self.refresh_proxy_list()

    def get_random(self):
        """
        Return random server from the list

        """
        self.refresh_proxy_list()
        return choice(self._servers)

    def get_next(self):
        "Return next server in the list"
        self.refresh_proxy_list()
        return self.server_iterator.next()

    def refresh_proxy_list(self):
        """
        Update proxy list.
        
        Re-read proxy file after each XX seconds.
        """
        
        if (self.read_time is None or
            (datetime.now() - self.read_time).seconds > self.read_timeout):
            self.load_proxy_list()
            self.read_time = datetime.now()
            self.server_iterator = itertools.cycle(self._servers)

    def load_proxy_list(self):
        """
        Load proxy list from specified source and validate loaded data.

        Each server could be in two forms:
        * simple: "server:port"
        * complex: "server:port:user:pwd"
        """

        if self.proxy_file:
            with open(self.proxy_file) as src:
                lines = src.read().splitlines()
        else:
            lines = self.server_list

        servers = []
        for line in lines:
            line = line.strip().replace(' ', '')
            if line:
                host, port, user, pwd = parse_proxyline(line)
                server_port = '%s:%s' % (host, port)
                if user:
                    user_pwd = '%s:%s' % (user, pwd)
                else:
                    user_pwd = None
                servers.append((server_port, user_pwd))
        self._servers = servers
