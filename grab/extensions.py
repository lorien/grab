from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from http.cookiejar import Cookie, CookieJar
from typing import Any, cast
from urllib.parse import urljoin, urlsplit

from .base import BaseExtension
from .document import Document
from .errors import GrabTooManyRedirectsError
from .request import HttpRequest
from .util.cookies import build_jar, create_cookie


class RedirectExtension(BaseExtension[HttpRequest, Document]):
    def __init__(self, cookiejar: None | CookieJar = None) -> None:
        self.cookiejar = cookiejar if cookiejar else CookieJar()
        self.ext_handlers = {
            "init-retry": self.process_init_retry,
            "retry": self.process_retry,
        }

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
            req.follow_location
            and (redir_url := self.find_redirect_url(resp)) is not None
        ):
            retry.state["redirect_count"] += 1
            if retry.state["redirect_count"] > req.redirect_limit:
                raise GrabTooManyRedirectsError()
            redir_url = urljoin(req.url, redir_url)
            req.url = redir_url
            return retry, req
        return None, None


class CookiesExtension(BaseExtension[HttpRequest, Document]):
    def __init__(self, cookiejar: None | CookieJar = None) -> None:
        self.cookiejar = cookiejar if cookiejar else CookieJar()
        self.ext_handlers = {
            "prepare_request_post": self.process_prepare_request_post,
            "request_cookies": self.process_request_cookies,
            "response_post": self.process_response_post,
        }

    def set_cookie(self, cookie: Cookie) -> None:
        self.cookiejar.set_cookie(cookie)

    def clear(self) -> None:
        """Clear all remembered cookies."""
        self.cookiejar.clear()

    def clone(self) -> CookiesExtension:
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
        for name, value in self.__dict__.items():
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

    def process_prepare_request_post(self, req: HttpRequest) -> None:
        self.update(req.cookies, req.url)

    def process_request_cookies(
        self, req: HttpRequest, jar: CookieJar  # pylint: disable=unused-argument
    ) -> None:
        for cookie in self.cookiejar:
            jar.set_cookie(cookie)

    def process_response_post(
        self, req: HttpRequest, doc: Document  # pylint: disable=unused-argument
    ) -> None:
        for item in doc.cookies:
            self.cookiejar.set_cookie(item)

    def reset(self) -> None:
        self.clear()
