from __future__ import annotations

import logging
from collections.abc import Mapping, MutableMapping
from copy import copy
from http.cookiejar import CookieJar
from pprint import pprint  # pylint: disable=unused-import
from secrets import SystemRandom
from typing import Any, cast, overload
from urllib.parse import urljoin, urlsplit

from user_agent import generate_user_agent

from grab.base import BaseTransport
from grab.document import Document
from grab.errors import GrabMisuseError, GrabTooManyRedirectsError
from grab.request import Request
from grab.transport import Urllib3Transport
from grab.util.cookies import build_jar, create_cookie
from grab.util.http import merge_with_dict

__all__ = ["Grab"]
logger = logging.getLogger(__name__)
logger_network = logging.getLogger("grab.network")
system_random = SystemRandom()


def copy_config(config: Mapping[str, Any]) -> MutableMapping[str, Any]:
    """Copy grab config with correct handling of mutable config values."""
    return {x: copy(y) for x, y in config.items()}


def default_grab_config() -> MutableMapping[str, Any]:
    return {
        "common_headers": None,
        "reuse_cookies": True,
    }


class Grab:
    __slots__ = ("config", "transport", "cookies", "_doc")
    document_class: type[Document] = Document

    def __init__(
        self,
        transport: None | BaseTransport | type[BaseTransport] = None,
        **kwargs: Any,
    ) -> None:
        self.config: MutableMapping[str, Any] = default_grab_config()
        self.config["common_headers"] = self.common_headers()
        self.transport = self.process_transport_option(transport, Urllib3Transport)
        self.cookies = CookieJar()
        if kwargs:
            self.setup(**kwargs)

    def process_transport_option(
        self,
        transport: None | BaseTransport | type[BaseTransport],
        default_transport: type[BaseTransport],
    ) -> BaseTransport:
        if transport and (
            not isinstance(transport, BaseTransport)
            and not issubclass(transport, BaseTransport)
        ):
            raise GrabMisuseError("Invalid Grab transport: {}".format(transport))
        if transport is None:
            return default_transport()
        if isinstance(transport, BaseTransport):
            return transport
        return transport()

    def clone(self, **kwargs: Any) -> Grab:
        r"""Create clone of Grab instance.

        Cloned instance will have the same state: cookies, referrer, response
        document data

        :param \\**kwargs: overrides settings of cloned grab instance
        """
        grab = Grab(transport=self.transport)
        grab.config = copy_config(self.config)
        grab.cookies = build_jar(list(self.cookies))  # building again makes a copy
        if kwargs:
            grab.setup(**kwargs)
        return grab

    def setup(self, **kwargs: Any) -> None:
        """Set up Grab instance configuration."""
        for key, val in kwargs.items():
            if key in self.config:
                self.config[key] = val
            else:
                raise GrabMisuseError("Unknown option: %s" % key)

    def merge_request_configs(
        self, request_config: MutableMapping[str, Any]
    ) -> MutableMapping[str, Any]:
        cfg: MutableMapping[str, Any] = {}
        for key, val in request_config.items():
            if key not in Request.init_keys:
                raise GrabMisuseError("Invalid request parameter: {}".format(key))
            cfg[key] = val
        for key in Request.init_keys:
            if key not in cfg:
                cfg[key] = None
        return cfg

    def prepare_request(self, request_config: MutableMapping[str, Any]) -> Request:
        """Configure all things to make real network request.

        This method is called before doing real request via transport extension.
        """
        self.transport.reset()
        cfg = self.merge_request_configs(request_config)
        # REASONABLE DEFAULTS
        if cfg["url"] is None:
            raise GrabMisuseError("Request URL must be set")
        if not cfg["method"]:
            cfg["method"] = "GET"
        if cfg["follow_location"] is None:
            cfg["follow_location"] = True
        # COMMON HEADERS EXTENSION
        if self.config["common_headers"]:
            cfg["headers"] = merge_with_dict(
                (cfg["headers"] or {}), self.config["common_headers"], replace=False
            )
        req = self.create_request_from_config(cfg)
        # COOKIES EXTENSION
        self.update_session_cookies(req.cookies, req.url)
        return req

    def create_request_from_config(self, config: MutableMapping[str, Any]) -> Request:
        for key in config:
            if key not in Request.init_keys:
                raise GrabMisuseError("Unknown request parameter: {}".format(key))
        return Request(**config)

    def update_session_cookies(
        self, cookies: Mapping[str, Any], request_url: str
    ) -> None:
        request_host = urlsplit(request_url).hostname
        if request_host and cookies:
            # If cookie item is provided in form with no domain specified,
            # then use domain value extracted from request URL
            for name, value in cookies.items():
                self.cookies.set_cookie(
                    create_cookie(name=name, value=value, domain=request_host)
                )

    def log_request(self, req: Request) -> None:
        """Log request details via logging system."""
        proxy_info = (
            " via proxy {}://{}{}".format(
                req.proxy_type, req.proxy, " with auth" if req.proxy_userpwd else ""
            )
            if req.proxy
            else ""
        )
        logger_network.debug("%s %s%s", req.method or "GET", req.url, proxy_info)

    def find_redirect_url(self, doc: Document) -> None | str:
        assert doc.headers is not None
        if doc.code in {301, 302, 303, 307, 308} and doc.headers["Location"]:
            return cast(str, doc.headers["Location"])
        return None

    @overload
    def request(self, url: Request, **request_kwargs: Any) -> Document:
        ...

    @overload
    def request(self, url: None | str = None, **request_kwargs: Any) -> Document:
        ...

    def request(
        self, url: None | str | Request = None, **request_kwargs: Any
    ) -> Document:
        """Perform network request.

        You can specify grab settings in ``**kwargs``.
        Any keyword argument will be passed to ``self.config``.

        Returns: ``Document`` objects.
        """
        if isinstance(url, Request):
            req = url
        else:
            if url is not None:
                request_kwargs["url"] = url
            req = self.prepare_request(request_kwargs)
        redir_count = 0
        while True:
            self.log_request(req)
            self.transport.request(req, self.cookies)
            with self.transport.wrap_transport_error():
                doc = self.process_request_result(req)
            if req.follow_location:
                redir_url = self.find_redirect_url(doc)
                if redir_url is not None:
                    redir_count += 1
                    if redir_count > req.redirect_limit:
                        raise GrabTooManyRedirectsError()
                    redir_url = urljoin(req.url, redir_url)
                    request_kwargs["url"] = redir_url
                    req = self.prepare_request(request_kwargs)
                    continue
            return doc

    def submit(self, doc: Document, **kwargs: Any) -> Document:
        """Submit current form.

        :param make_request: if `False` then grab instance will be
            configured with form post data but request will not be
            performed

        For details see `Document.submit()` method
        """
        url, method, is_multipart, fields = doc.get_form_request(**kwargs)
        return self.request(
            url=url,
            method=method,
            multipart=is_multipart,
            fields=fields,
        )

    def process_request_result(self, req: Request) -> Document:
        """Process result of real request performed via transport extension."""
        doc = self.transport.prepare_response(req, document_class=self.document_class)
        if self.config["reuse_cookies"]:
            for item in doc.cookies:
                self.cookies.set_cookie(item)
        return doc

    @classmethod
    def common_headers(cls) -> dict[str, str]:
        """Build headers which sends typical browser."""
        return {
            "Accept": "text/xml,application/xml,application/xhtml+xml"
            ",text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.%d"
            % system_random.randint(2, 5),
            "Accept-Language": "en-us,en;q=0.%d" % (system_random.randint(5, 9)),
            "Accept-Charset": "utf-8,windows-1251;q=0.7,*;q=0.%d"
            % system_random.randint(5, 7),
            "Keep-Alive": "300",
            "User-Agent": generate_user_agent(),
        }

    def clear_cookies(self) -> None:
        """Clear all remembered cookies."""
        self.cookies.clear()

    def __getstate__(self) -> dict[str, Any]:
        state = {}
        for slot_name in self.__slots__:
            if slot_name == "cookies":
                state["_cookies_items"] = list(self.cookies)
            else:
                state[slot_name] = getattr(self, slot_name)
        return state

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        for key, value in state.items():
            if key == "_cookies_items":
                self.cookies = build_jar(value)
            else:
                if key not in self.__slots__:
                    raise ValueError("Key '{}' is not in __slots__'".format(key))
                setattr(self, key, value)
