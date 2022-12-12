from __future__ import annotations

import itertools
import logging
import re
import typing
from collections.abc import Iterator
from random import randint
from typing import IO, Any, NamedTuple, cast
from urllib.error import URLError
from urllib.request import urlopen

from grab.error import GrabError

RE_SIMPLE_PROXY = re.compile(r"^([^:]+):(\d+)$")
RE_AUTH_PROXY = re.compile(r"^([^:]+):(\d+):([^:]+):([^:]+)$")
PROXY_FIELDS = ("host", "port", "username", "password", "proxy_type")
logger = logging.getLogger("grab.proxylist")


class Proxy(NamedTuple):
    host: str
    port: int
    username: None | str
    password: None | str
    proxy_type: str

    def get_address(self) -> str:
        return "%s:%s" % (self.host, self.port)

    def get_userpwd(self) -> None | str:
        if self.username:
            return "%s:%s" % (self.username, self.password or "")
        return None


class InvalidProxyLine(GrabError):
    pass


def parse_proxy_line(line: str) -> tuple[str, int, None | str, None | str]:
    """Parse proxy details from the raw text line.

    The text line could be in one of the following formats:
    * host:port
    * host:port:username:password
    """
    line = line.strip()
    match = RE_SIMPLE_PROXY.search(line)
    if match:
        return match.group(1), int(match.group(2)), None, None

    match = RE_AUTH_PROXY.search(line)
    if match:
        host, port, user, pwd = match.groups()
        return host, int(port), user, pwd

    raise InvalidProxyLine("Invalid proxy line: %s" % line)


def parse_raw_list_data(
    data: str, proxy_type: str = "http", proxy_userpwd: None | str = None
) -> Iterator[Proxy]:
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
    def __init__(
        self,
        proxy_type: str = "http",
        proxy_userpwd: None | str = None,
        **kwargs: Any,
    ) -> None:
        kwargs["proxy_type"] = proxy_type
        kwargs["proxy_userpwd"] = proxy_userpwd
        self.config = kwargs

    def load_raw_data(self) -> str:
        raise NotImplementedError

    def load(self) -> list[Proxy]:
        return list(
            parse_raw_list_data(
                self.load_raw_data(),
                proxy_type=self.config["proxy_type"],
                proxy_userpwd=self.config["proxy_userpwd"],
            )
        )


class FileProxySource(BaseProxySource):
    """Load list from the file."""

    def __init__(self, path: str, **kwargs: Any) -> None:
        self.path = path
        super().__init__(**kwargs)

    def load_raw_data(self) -> str:
        with open(self.path, encoding="utf-8") as inp:
            return inp.read()


class WebProxySource(BaseProxySource):
    """Load list from web resource."""

    def __init__(self, url: str, **kwargs: Any) -> None:
        self.url = url
        super().__init__(**kwargs)

    def load_raw_data(self) -> str:
        limit = 3
        for ntry in range(limit):
            try:
                with urlopen(self.url, timeout=3) as inp:
                    return cast(IO[bytes], inp).read().decode("utf-8", "ignore")
            except URLError:
                if ntry >= (limit - 1):
                    raise
                logger.debug(
                    "Failed to retrieve proxy list from %s. Retrying.", self.url
                )
        raise Exception("Could not happen")


class ListProxySource(BaseProxySource):
    """Load list from python list of strings."""

    def __init__(self, items: list[str], **kwargs: Any) -> None:
        self.items = items
        super().__init__(**kwargs)

    def load_raw_data(self) -> str:
        return "\n".join(self.items)


class ProxyList:
    """Class to work with proxy list."""

    def __init__(self, source: None | BaseProxySource = None) -> None:
        self._source = source
        self._list: list[Proxy] = []
        self._list_iter: None | Iterator[Proxy] = None

    def set_source(self, source: BaseProxySource) -> None:
        """Set the proxy source and use it to load proxy list."""
        self._source = source
        self.load()

    def load_file(self, path: str, **kwargs: Any) -> None:
        """Load proxy list from file."""
        self.set_source(FileProxySource(path, **kwargs))

    def load_url(self, url: str, **kwargs: Any) -> None:
        """Load proxy list from web document."""
        self.set_source(WebProxySource(url, **kwargs))

    def load_list(self, items: list[str], **kwargs: Any) -> None:
        """Load proxy list from python list."""
        self.set_source(ListProxySource(items, **kwargs))

    def load(self) -> None:
        """Load proxy list from configured proxy source."""
        assert self._source is not None
        self._list = self._source.load()
        self._list_iter = itertools.cycle(self._list)

    def get_random_proxy(self) -> Proxy:
        """Return random proxy."""
        idx = randint(0, len(self._list) - 1)
        return self._list[idx]

    def get_next_proxy(self) -> Proxy:
        """Return next proxy."""
        # pylint: disable=deprecated-typing-alias
        return next(cast(typing.Iterator[Proxy], self._list_iter))

    def size(self) -> int:
        """Return number of proxies in the list."""
        return len(self._list)

    def __iter__(self) -> Iterator[Proxy]:
        return iter(self._list)

    def __len__(self) -> int:
        return len(self._list)

    def __getitem__(self, key: int) -> Proxy:
        return self._list[key]
