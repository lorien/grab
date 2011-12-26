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

READ_TIMEOUT = 60 * 10
RE_SIMPLE_PROXY = re.compile(r'^([^:]+):([^:]+)$')
RE_AUTH_PROXY = re.compile(r'^([^:]+):([^:]+):([^:]+):([^:]+)$')

class ProxyList(object):
    """
    Class to work with proxy list which 
    is stored in the plain text file.
    """

    def __init__(self, proxy_file, proxy_type, read_timeout=None):
        self.proxy_file = proxy_file
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
        return choice(self.servers)

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
            self.server_iterator = itertools.cycle(self.servers)

    def load_proxy_list(self):
        """
        Load proxy servers from file.

        Each server could be in two forms:
        * simple: "server:port"
        * complex: "server:port:user:pwd"
        """

        with open(self.proxy_file) as src:
            servers = []
            for line in src:
                line = line.strip().replace(' ', '')
                if line:
                    match = RE_SIMPLE_PROXY.search(line)
                    if match:
                        host, port = match.groups()
                        server_port = '%s:%s' % (host, port)
                        servers.append((server_port, None))
                    else:
                        match = RE_AUTH_PROXY.search(line)
                        if match:
                            host, port, user, pwd = match.groups()
                            server_port = '%s:%s' % (host, port)
                            user_pwd = '%s:%s' % (user, pwd)
                            servers.append((server_port, user_pwd))
                    if not match:
                        logging.error('Invalid proxy line: %s' % line)
            self.servers = servers
