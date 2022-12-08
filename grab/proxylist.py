import itertools
import logging
import re
from collections import namedtuple
from random import randint
from urllib.error import URLError
from urllib.request import urlopen

from grab.error import GrabError

RE_SIMPLE_PROXY = re.compile(r"^([^:]+):([^:]+)$")
RE_AUTH_PROXY = re.compile(r"^([^:]+):([^:]+):([^:]+):([^:]+)$")
PROXY_FIELDS = ("host", "port", "username", "password", "proxy_type")
logger = logging.getLogger("grab.proxylist")  # pylint: disable=invalid-name


class Proxy(namedtuple("Proxy", PROXY_FIELDS)):
    def get_address(self):
        return "%s:%s" % (self.host, self.port)

    def get_userpwd(self):
        if self.username:
            return "%s:%s" % (self.username, self.password or "")
        return None


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

    raise InvalidProxyLine("Invalid proxy line: %s" % line)


def parse_raw_list_data(data, proxy_type="http", proxy_userpwd=None):
    """Iterate over proxy servers found in the raw data."""
    if not isinstance(data, str):
        data = data.decode("utf-8")
    for orig_line in data.splitlines():
        line = orig_line.strip().replace(" ", "")
        if line and not line.startswith("#"):
            try:
                host, port, username, password = parse_proxy_line(line)
            except InvalidProxyLine as ex:
                logger.error(ex)
            else:
                if username is None and proxy_userpwd is not None:
                    username, password = proxy_userpwd.split(":")
                yield Proxy(host, port, username, password, proxy_type)


class BaseProxySource:
    def __init__(self, proxy_type="http", proxy_userpwd=None, **kwargs):
        kwargs["proxy_type"] = proxy_type
        kwargs["proxy_userpwd"] = proxy_userpwd
        self.config = kwargs

    def load_raw_data(self):
        raise NotImplementedError

    def load(self):
        data = self.load_raw_data()
        return list(
            parse_raw_list_data(
                data,
                proxy_type=self.config["proxy_type"],
                proxy_userpwd=self.config["proxy_userpwd"],
            )
        )


class FileProxySource(BaseProxySource):
    """Load list from the file."""

    def __init__(self, path, **kwargs):
        self.path = path
        super().__init__(**kwargs)

    def load_raw_data(self):
        with open(self.path, encoding="utf-8") as inp:
            return inp.read()


class WebProxySource(BaseProxySource):
    """Load list from web resource."""

    def __init__(self, url, **kwargs):
        self.url = url
        super().__init__(**kwargs)

    def load_raw_data(self):  # pylint: disable=inconsistent-return-statements
        limit = 3
        for ntry in range(limit):
            try:
                with urlopen(self.url, timeout=3) as inp:
                    return inp.read().decode("utf-8", "ignore")
            except URLError:
                if ntry >= (limit - 1):
                    raise
                logger.debug(
                    "Failed to retrieve proxy list from %s. Retrying.", self.url
                )


class ListProxySource(BaseProxySource):
    """Load list from python list of strings."""

    def __init__(self, items, **kwargs):
        self.items = items
        super().__init__(**kwargs)

    def load_raw_data(self):
        return "\n".join(self.items)


class ProxyList:
    """Class to work with proxy list."""

    def __init__(self, source=None):
        self._source = source
        self._list = []
        self._list_iter = None

    def set_source(self, source):
        """Set the proxy source and use it to load proxy list."""
        self._source = source
        self.load()

    def load_file(self, path, **kwargs):
        """Load proxy list from file."""
        self.set_source(FileProxySource(path, **kwargs))

    def load_url(self, url, **kwargs):
        """Load proxy list from web document."""
        self.set_source(WebProxySource(url, **kwargs))

    def load_list(self, items, **kwargs):
        """Load proxy list from python list."""
        self.set_source(ListProxySource(items, **kwargs))

    def load(self):
        """Load proxy list from configured proxy source."""
        self._list = self._source.load()
        self._list_iter = itertools.cycle(self._list)

    def get_random_proxy(self):
        """Return random proxy."""
        idx = randint(0, len(self._list) - 1)
        return self._list[idx]

    def get_next_proxy(self):
        """Return next proxy."""
        return next(self._list_iter)

    def size(self):
        """Return number of proxies in the list."""
        return len(self._list)

    def __iter__(self):
        return iter(self._list)

    def __len__(self):
        return len(self._list)

    def __getitem__(self, key):
        return self._list[key]
