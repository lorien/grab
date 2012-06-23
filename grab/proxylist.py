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
import re
import logging
from copy import deepcopy
import time
import logging

from error import GrabError, GrabMisuseError

logger = logging.getLogger('grab.proxylist')

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


class TextFileSource(object):
    source_type = 'text_file'

    def __init__(self, filename, read_timeout=READ_TIMEOUT, proxy_type='http'):
        self.filename = filename
        self.proxy_type = proxy_type
        self.read_timeout = read_timeout

    def load(self):
        """
        Load proxy list from specified source and validate loaded data.

        Each server could be in two forms:
        * simple: "server:port"
        * complex: "server:port:user:pwd"
        """

        with open(self.filename) as src:
            lines = src.read().splitlines()

        servers = []
        for line in lines:
            line = line.strip().replace(' ', '')
            if line:
                host, port, user, pwd = parse_proxyline(line)
                server = '%s:%s' % (host, port)
                if user:
                    user_pwd = '%s:%s' % (user, pwd)
                else:
                    user_pwd = None
                servers.append((server, user_pwd, self.proxy_type))
        self.read_time = time.time()
        self.server_list = servers
        self.server_list_iterator = itertools.cycle(self.server_list)

    def reload(self):
        """
        Update proxy list.
        
        Re-read proxy file after each XX seconds.
        """
        
        if (self.read_time is None or
            (time.time() - self.read_time) > self.read_timeout):
            logger.debug('Reloading proxy list')
            self.load()


SOURCE_LIST = {
    'text_file': TextFileSource,
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
        :param proxy_type: default type of proxy (if proxy source does not provide
            this information)
        :param **kwargs: any additional aruguments goes to specific proxy load method 
        """

        self.init_kwargs = deepcopy(kwargs)

        try:
            source_class = SOURCE_LIST[source_type]
        except AttributeError:
            raise GrabMisuseError('Unknown proxy source type: %s' % source_type)
        self.source = source_class(source, proxy_type=proxy_type, **kwargs)
        self.source.load()

    def get_random(self):
        """
        Return random server from the list
        """

        self.source.reload()
        return choice(self.source.server_list)

    def get_next(self):
        """
        Return next server in the list.
        """

        logger.debug('Changing proxy')
        self.source.reload()
        return self.source.server_list_iterator.next()
