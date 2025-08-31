from __future__ import annotations

import weakref
from collections.abc import Mapping, MutableMapping
from http.cookiejar import Cookie, CookieJar
from typing import Any, cast
from urllib.parse import urljoin, urlsplit

from .base import BaseClient, BaseExtension
from .document import Document
from .errors import GrabTooManyRedirectsError
from .request import HttpRequest
from .util.cookies import build_cookie_header, build_jar, create_cookie


class RedirectExtension(BaseExtension[HttpRequest, Document]):
    def __init__(self) -> None:
        self.ext_handlers = {
            "init-retry": self.process_init_retry,
            "retry": self.process_retry,
        }

    def __get__(
        self,
        obj: BaseClient[HttpRequest, Document],
        objtype: None | type[BaseClient[HttpRequest, Document]] = None,
    ) -> RedirectExtension:
        return self

    def find_redirect_url(self, doc: Document) -> None | str:
        assert doc.headers is not None
        if doc.code in {301, 302, 303, 307, 308} and doc.headers["Location"]:
            return cast(str, doc.headers["Location"])
        return None

    def process_init_retry(self, retry: Any) -> None:
        retry.state["redirect_count"] = 0

    def reset(self) -> None:
        pass

    def process_retry(
        self, retry: Any, req: HttpRequest, resp: Document
    ) -> tuple[None, None] | tuple[Any, HttpRequest]:
        if (
            req.process_redirect
            and (redir_url := self.find_redirect_url(resp)) is not None
        ):
            retry.state["redirect_count"] += 1
            if retry.state["redirect_count"] > req.redirect_limit:
                raise GrabTooManyRedirectsError
            redir_url = urljoin(req.url, redir_url)
            req.url = redir_url
            return retry, req
        return None, None


class CookiesStore:
    __slots__ = ("cookiejar", "ext_handlers")

    def __init__(self, cookiejar: None | CookieJar = None) -> None:
        self.cookiejar = cookiejar if cookiejar else CookieJar()
        self.ext_handlers = {
            "request:pre": self.process_request_pre,
            "response:post": self.process_response_post,
        }

    def process_request_pre(self, req: HttpRequest) -> None:
        self.update(req.cookies, req.url)
        if hdr := build_cookie_header(self.cookiejar, req.url, req.headers):
            if req.headers.get("Cookie"):
                raise ValueError(
                    "Could not configure request with session cookies"
                    " because it has already Cookie header"
                )
            req.cookie_header = hdr

    def process_response_post(
        self,
        req: HttpRequest,  # noqa: ARG002 pylint: disable=unused-argument
        doc: Document,
    ) -> None:
        for item in doc.cookies:
            self.cookiejar.set_cookie(item)

    def reset(self) -> None:
        self.clear()

    def set_cookie(self, cookie: Cookie) -> None:
        self.cookiejar.set_cookie(cookie)

    def clear(self) -> None:
        """Clear all remembered cookies."""
        self.cookiejar.clear()

    def clone(self) -> CookiesStore:
        return self.__class__(build_jar(list(self.cookiejar)))

    def update(self, cookies: Mapping[str, Any], request_url: str) -> None:
        request_host = urlsplit(request_url).hostname
        if request_host and cookies:
            # If cookie item is provided in form with no domain specified,
            # then use domain value extracted from request URL
            for name, value in cookies.items():
                self.cookiejar.set_cookie(
                    create_cookie(name=name, value=value, domain=request_host)
                )

    def __getstate__(self) -> MutableMapping[str, Any]:
        state = {}
        for name in self.__slots__:
            value = getattr(self, name)
            if name == "cookiejar":
                state["_cookiejar_items"] = list(value)
            else:
                state[name] = value
        return state

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        for name, value in state.items():
            if name == "_cookiejar_items":
                self.cookiejar = build_jar(value)
            else:
                setattr(self, name, value)


class CookiesExtension(BaseExtension[HttpRequest, Document]):
    __slots__ = ()

    owner_store_reg: MutableMapping[
        BaseClient[HttpRequest, Document], CookiesStore
    ] = {}

    def __init__(self) -> None:
        self.owners: weakref.WeakKeyDictionary[
            BaseClient[HttpRequest, Document], CookiesStore
        ] = weakref.WeakKeyDictionary()

    def __get__(
        self,
        obj: BaseClient[HttpRequest, Document],
        objtype: None | type[BaseClient[HttpRequest, Document]] = None,
    ) -> CookiesStore:
        return self.owners.setdefault(obj, CookiesStore())

    def reset(self) -> None:
        pass
