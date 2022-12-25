from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from http.cookiejar import Cookie, CookieJar
from typing import Any
from urllib.parse import urlsplit

from .base import BaseExtension
from .document import Document
from .request import Request
from .util.cookies import build_jar, create_cookie


class CookiesExtension(BaseExtension):
    mount_points = ["request_cookies", "prepare_request_post", "response_post"]

    def __init__(self, cookiejar: None | CookieJar = None) -> None:
        self.cookiejar = cookiejar if cookiejar else CookieJar()

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

    def process_prepare_request_post(self, req: Request) -> None:
        self.update(req.cookies, req.url)

    def process_request_cookies(
        self, req: Request, jar: CookieJar  # pylint: disable=unused-argument
    ) -> None:
        for cookie in self.cookiejar:
            jar.set_cookie(cookie)

    def process_response_post(
        self, req: Request, doc: Document  # pylint: disable=unused-argument
    ) -> None:
        for item in doc.cookies:
            self.cookiejar.set_cookie(item)

    def reset(self) -> None:
        self.clear()
