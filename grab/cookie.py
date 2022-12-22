"""This module provides things to operate with cookies.

Manuals:

* http://docs.python.org/2/library/cookielib.html#cookie-objects

Some code got from
    https://github.com/kennethreitz/requests/blob/master/requests/cookies.py
"""
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from copy import copy
from http.client import HTTPMessage
from http.cookiejar import Cookie, CookieJar
from typing import Any, cast
from urllib.parse import urlparse, urlunparse
from urllib.request import Request

from urllib3._collections import HTTPHeaderDict

from grab.error import GrabMisuseError

COOKIE_ATTRS = (
    "name",
    "value",
    "version",
    "port",
    "domain",
    "path",
    "secure",
    "expires",
    "discard",
    "comment",
    "comment_url",
    "rfc2109",
)


# Reference:
# https://docs.python.org/3/library/http.cookiejar.html#http.cookiejar.CookieJar.add_cookie_header
# Source:
# https://github.com/kennethreitz/requests/blob/master/requests/cookies.py
class MockRequest:
    """Wraps a `requests.Request` to mimic a `urllib2.Request`.

    The code in `cookielib.CookieJar` expects this interface in order to
    correctly manage cookie policies, i.e., determine whether a cookie can be
    set, given the domains of the request and the cookie.
    The original request object is read-only. The client is responsible for
    collecting the new headers via `get_new_headers()` and interpreting them
    appropriately. You probably want `get_cookie_header`, defined below.
    """

    def __init__(self, url: str, headers: dict[str, str]):
        self._url = url
        self._headers = headers
        self._new_headers: dict[str, Any] = {}
        self.type = urlparse(self._url).scheme

    def get_type(self) -> str:
        return self.type

    def get_host(self) -> str:
        return urlparse(self._url).netloc

    def get_origin_req_host(self) -> str:
        return self.get_host()

    def get_full_url(self) -> str:
        # Only return the response's URL if the user hadn't set the Host
        # header
        if not self._headers.get("Host"):
            return self._url
        # If they did set it, retrieve it and reconstruct the expected domain
        host = self._headers["Host"]
        parsed = urlparse(self._url)
        # Reconstruct the URL as we expect it
        return urlunparse(
            [
                parsed.scheme,
                host,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            ]
        )

    def is_unverifiable(self) -> bool:
        return True

    def has_header(self, name: str) -> bool:
        return name in self._headers or name in self._new_headers

    def get_header(self, name: str, default: Any = None) -> str:
        return self._headers.get(name, self._new_headers.get(name, default))

    def add_header(self, key: str, val: str) -> None:
        """Cookielib has no legitimate use for this method.

        Add it back if you find one.
        """
        raise NotImplementedError(
            "Cookie headers should be added with add_unredirected_header()"
        )

    def add_unredirected_header(self, name: str, value: str) -> None:
        self._new_headers[name] = value

    def get_new_headers(self) -> dict[str, str]:
        return self._new_headers

    @property
    def unverifiable(self) -> bool:
        return self.is_unverifiable()

    @property
    def origin_req_host(self) -> str:
        return self.get_origin_req_host()

    @property
    def host(self) -> str:
        return self.get_host()


# https://github.com/kennethreitz/requests/blob/master/requests/cookies.py
class MockResponse:
    """Wraps a `httplib.HTTPMessage` to mimic a `urllib.addinfourl`.

    ...what? Basically, expose the parsed HTTP headers from the server response
    the way `cookielib` expects to see them.
    """

    def __init__(self, headers: HTTPMessage | HTTPHeaderDict) -> None:
        """Make a MockResponse for `cookielib` to read.

        :param headers: a httplib.HTTPMessage or analogous carrying the headers
        """
        self._headers = headers

    def info(self) -> HTTPMessage | HTTPHeaderDict:
        return self._headers


def create_cookie(  # pylint: disable=too-many-arguments, too-many-locals
    # required
    name: str,
    value: str,
    domain: str,
    # non required
    comment: None | str = None,
    comment_url: None | str = None,
    discard: bool = True,
    domain_initial_dot: None | bool = None,
    domain_specified: None | bool = None,
    expires: None | int = None,
    path: str = "/",
    path_specified: None | bool = None,
    port: None | int = None,
    port_specified: None | bool = None,
    rest: None | dict[str, Any] = None,
    rfc2109: bool = False,
    secure: bool = False,
    version: int = 0,
    httponly: None | bool = None,
) -> Cookie:
    """Create cookielib.Cookie instance."""
    # See also type hints for Cookie at
    # https://github.com/python/typeshed/blob/main/stdlib/http/cookiejar.pyi
    if domain == "localhost":
        domain = ""
    if rest is None:
        new_rest = {}
    else:
        new_rest = copy(rest)
        if "HttpOnly" not in new_rest:
            new_rest["HttpOnly"] = httponly
    if port_specified is None:
        port_specified = port is not None
    if domain_specified is None:
        domain_specified = domain is not None
    if domain_initial_dot is None:
        domain_initial_dot = domain.startswith(".")
    if path_specified is None:
        path_specified = path is not None
    return Cookie(
        # from required scope
        name=name,
        value=value,
        domain=domain,
        # from non required scope
        comment=comment,
        comment_url=comment_url,
        discard=discard,
        domain_initial_dot=domain_initial_dot,
        domain_specified=domain_specified,
        expires=expires,
        path=path,
        path_specified=path_specified,
        port=str(port) if port else None,  # typeshed bundled with mypy wants str type
        port_specified=port_specified,
        rest=new_rest,
        rfc2109=rfc2109,
        secure=secure,
        version=version,
    )


class CookieManager:
    """Class to operate cookies of Grab instance.

    Each Grab instance has `cookies` attribute that is instance of
    `CookieManager` class.

    That class contains helpful methods to create, load, save cookies from/to
    different places.
    """

    __slots__ = ("cookiejar",)

    def __init__(self, cookiejar: None | CookieJar = None) -> None:
        if cookiejar is not None:
            self.cookiejar = cookiejar
        else:
            self.cookiejar = CookieJar()

    def set(self, name: str, value: str, domain: str, **kwargs: Any) -> None:
        """Add new cookie or replace existing cookie with same parameters.

        :param name: name of cookie
        :param value: value of cookie
        :param kwargs: extra attributes of cookie
        """
        if domain == "localhost":
            domain = ""

        self.cookiejar.set_cookie(create_cookie(name, value, domain, **kwargs))

    def update(self, cookies: CookieJar | CookieManager) -> None:
        if isinstance(cookies, CookieJar):
            for cookie in cookies:
                self.cookiejar.set_cookie(cookie)
        elif isinstance(cookies, CookieManager):
            for cookie in cookies.cookiejar:
                self.cookiejar.set_cookie(cookie)
        else:
            raise GrabMisuseError(
                "Unknown type of cookies argument: %s" % type(cookies)
            )

    @classmethod
    def from_cookie_list(cls, clist: Sequence[Cookie]) -> CookieManager:
        jar = CookieJar()
        for cookie in clist:
            jar.set_cookie(cookie)
        return cls(jar)

    def clear(self) -> None:
        self.cookiejar = CookieJar()

    def __getstate__(self) -> dict[str, Any]:
        state = {}
        for cls in type(self).mro():
            cls_slots = getattr(cls, "__slots__", ())
            for slot in cls_slots:
                if hasattr(self, slot):
                    state[slot] = getattr(self, slot)

        state["_cookiejar_cookies"] = list(self.cookiejar)
        del state["cookiejar"]

        return state

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        self.cookiejar = CookieJar()
        for cookie in state["_cookiejar_cookies"]:
            self.cookiejar.set_cookie(cookie)
        for key, value in state.items():
            if key != "_cookiejar_cookies":
                setattr(self, key, value)

    def __getitem__(self, key: str) -> None | str:
        for cookie in self.cookiejar:
            if cookie.name == key:
                return cookie.value
        raise KeyError

    def items(self) -> list[tuple[str, None | str]]:
        res = []
        for cookie in self.cookiejar:
            res.append((cookie.name, cookie.value))
        return res

    def load_from_file(self, path: str) -> None:
        """Load cookies from the file.

        Content of file should be a JSON-serialized list of dicts.
        """
        with open(path, encoding="utf-8") as inf:
            data = inf.read()
            items = json.loads(data) if data else {}
        for item in items:
            extra = {
                x: y for x, y in item.items() if x not in ["name", "value", "domain"]
            }
            self.set(item["name"], item["value"], item["domain"], **extra)

    def get_dict(self) -> list[dict[str, Any]]:
        res = []
        for cookie in self.cookiejar:
            res.append({x: getattr(cookie, x) for x in COOKIE_ATTRS})
        return res

    def save_to_file(self, path: str) -> None:
        """Dump all cookies to file.

        Cookies are dumped as JSON-serialized dict of keys and values.
        """
        with open(path, "w", encoding="utf-8") as out:
            out.write(json.dumps(self.get_dict()))

    def get_cookie_header(self, url: str, headers: dict[str, str]) -> None | str:
        # :param req: object with httplib.Request interface
        #    Actually, it have to have `url` and `headers` attributes
        mocked_req = MockRequest(url, headers)
        self.cookiejar.add_cookie_header(cast(Request, mocked_req))
        return mocked_req.get_new_headers().get("Cookie")
