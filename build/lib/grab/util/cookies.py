"""THe module provides things to operate with cookies.

Manuals:

* http://docs.python.org/2/library/cookielib.html#cookie-objects

Some code got from
    https://github.com/kennethreitz/requests/blob/master/requests/cookies.py
"""
from __future__ import annotations

import urllib.request
from collections.abc import Mapping, Sequence
from copy import copy
from http.client import HTTPMessage, HTTPResponse
from http.cookiejar import Cookie, CookieJar
from typing import Any, cast
from urllib.parse import urlparse, urlunparse

from urllib3._collections import HTTPHeaderDict


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

    def __init__(self, url: str, headers: dict[str, str]) -> None:
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


def create_cookie(  # noqa: PLR0913 pylint: disable=too-many-arguments, too-many-locals
    *,
    name: str,
    value: str,
    domain: str,
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


def build_cookie_header(
    cookiejar: CookieJar, url: str, headers: Mapping[str, str]
) -> None | str:
    """Build HTTP Cookie header value for given cookies."""
    mocked_req = MockRequest(url, dict(headers))
    cookiejar.add_cookie_header(cast(urllib.request.Request, mocked_req))
    return mocked_req.get_new_headers().get("Cookie")


def build_jar(cookies: Sequence[Cookie]) -> CookieJar:
    jar = CookieJar()
    for item in cookies:
        jar.set_cookie(item)
    return jar


def extract_response_cookies(
    req_url: str,
    req_headers: Mapping[str, Any] | HTTPMessage | HTTPHeaderDict,
    response_headers: HTTPMessage | HTTPHeaderDict,
) -> Sequence[Cookie]:
    jar = CookieJar()
    jar.extract_cookies(
        cast(HTTPResponse, MockResponse(response_headers)),
        cast(urllib.request.Request, MockRequest(req_url, dict(req_headers))),
    )
    return list(jar)
