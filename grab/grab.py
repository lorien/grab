from __future__ import annotations

import logging
import threading
from collections.abc import Mapping, MutableMapping
from copy import copy
from datetime import datetime
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
from grab.util.cookies import create_cookie
from grab.util.http import merge_with_dict

__all__ = ["Grab"]
MUTABLE_CONFIG_KEYS = ["fields", "headers", "cookies"]
logger = logging.getLogger("grab.base")
logger_network = logging.getLogger("grab.network")
system_random = SystemRandom()


def copy_config(config: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Copy grab config with correct handling of mutable config values."""
    cloned_config = {}
    for key, val in config.items():
        if key == "request":
            cloned_config[key] = copy_config(val)
        elif key in MUTABLE_CONFIG_KEYS:
            cloned_config[key] = copy(val)
        else:
            cloned_config[key] = val
    return cloned_config


DEFAULT_REQUEST_CONFIG = {
    # Request Properties
    "method": None,
    "url": None,
    "proxy": None,
    "proxy_type": None,
    "proxy_userpwd": None,
    "headers": None,
    "cookies": None,
    "timeout": None,
    "encoding": None,
    "document_type": None,
    "body": None,
    "fields": None,
    "multipart": None,
    # Needs refactoring
    "redirect_limit": None,  # -> Retry/Redirect object
    "follow_location": None,  # -> Redirect/Redirect object
}


def default_grab_config() -> MutableMapping[str, Any]:
    return {
        "request": {},
        "common_headers": None,
        "reuse_cookies": True,
        "state": {},
    }


class Grab:
    __slots__ = (
        "config",
        "transport",
        "request_method",
        "cookies",
        "meta",
        "_doc",
    )
    document_class: type[Document] = Document
    # Attributes which should be processed when Grab instance is cloned

    def __init__(
        self,
        transport: None | BaseTransport | type[BaseTransport] = None,
        **kwargs: Any,
    ) -> None:
        self.transport = self.process_transport_option(transport, Urllib3Transport)
        self._doc: None | Document = None
        self.config: MutableMapping[str, Any] = default_grab_config()
        self.config["common_headers"] = self.common_headers()
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

    @property
    def doc(self) -> None | Document:
        return self._doc

    @doc.setter
    def doc(self, obj: Document) -> None:
        self._doc = obj

    def clone(self, **kwargs: Any) -> Grab:
        r"""Create clone of Grab instance.

        Cloned instance will have the same state: cookies, referrer, response
        document data

        :param \\**kwargs: overrides settings of cloned grab instance
        """
        # TODO: self.transport must be cloned ?
        grab = Grab(transport=self.transport)
        grab.config = self.dump_config()
        grab.doc = self.doc.copy() if self.doc else None
        jar = CookieJar()
        for item in self.cookies:
            jar.set_cookie(item)
        grab.cookies = jar
        if kwargs:
            grab.setup(**kwargs)
        return grab

    def dump_config(self) -> MutableMapping[str, Any]:
        """Make clone of current config."""
        conf = copy_config(self.config)
        conf["state"] = {
            "cookiejar_cookies": list(self.cookies),
        }
        return conf

    def load_config(self, config: MutableMapping[str, Any]) -> None:
        """Configure grab instance with external config object."""
        self.config = copy_config(config)
        if "cookiejar_cookies" in config["state"]:
            jar = CookieJar()
            for cookie in config["state"]["cookiejar_cookies"]:
                jar.set_cookie(cookie)
            self.cookies = jar

    def setup(self, **kwargs: Any) -> None:
        """Set up Grab instance configuration."""
        for key, val in kwargs.items():
            if key in self.config:
                self.config[key] = val
            elif key in DEFAULT_REQUEST_CONFIG:
                self.config["request"][key] = val
            else:
                raise GrabMisuseError("Unknown option: %s" % key)

    def merge_request_configs(
        self, request_config: MutableMapping[str, Any]
    ) -> MutableMapping[str, Any]:
        cfg: MutableMapping[str, Any] = {}
        for key, val in request_config.items():
            if key not in DEFAULT_REQUEST_CONFIG:
                raise GrabMisuseError("Invalid request parameter: {}".format(key))
            cfg[key] = val
        for key, val in self.config["request"].items():
            if key not in cfg:
                cfg[key] = val
        for key, val in DEFAULT_REQUEST_CONFIG.items():
            if key not in cfg:
                cfg[key] = val
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
        self.sync_cookie_manager_with_request_cookies(req.cookies, req.url)
        return req

    def create_request_from_config(self, config: MutableMapping[str, Any]) -> Request:
        for key in config:
            if key not in DEFAULT_REQUEST_CONFIG:
                raise GrabMisuseError("Unknown request parameter: {}".format(key))
        return Request(**config)

    def sync_cookie_manager_with_request_cookies(
        self,
        cookies: Mapping[str, Any],
        request_url: str,
    ) -> None:
        request_host = urlsplit(request_url).hostname
        if request_host and cookies:
            # If cookie item is provided in form with no domain specified,
            # then use domain value extracted from request URL
            for name, value in cookies.items():
                self.cookies.set_cookie(
                    create_cookie(name=name, value=value, domain=request_host)
                )

    def log_request(self, req: Request, extra: str = "") -> None:
        """Send request details to logging system."""
        thread_name = threading.current_thread().name.lower()
        proxy_info = (
            " via {} proxy of type {}{}".format(
                req.proxy,
                req.proxy_type,
                " with auth" if req.proxy_userpwd else "",
            )
            if req.proxy
            else ""
        )
        logger_network.debug(
            "%s%s%s %s%s",
            "" if (thread_name == "mainthread") else "[{}] ".format(thread_name),
            "[{}]".format(extra) if extra else "",
            req.method or "GET",
            req.url,
            proxy_info,
        )

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

    def submit(self, **kwargs: Any) -> Document:
        """Submit current form.

        :param make_request: if `False` then grab instance will be
            configured with form post data but request will not be
            performed

        For details see `Document.submit()` method
        """
        assert self.doc is not None
        url, method, is_multipart, fields = self.doc.get_form_request(**kwargs)
        return self.request(
            url=url,
            method=method,
            multipart=is_multipart,
            fields=fields,
        )

    def process_request_result(self, req: Request) -> Document:
        """Process result of real request performed via transport extension."""
        now = datetime.utcnow()

        self.doc = self.transport.prepare_response(
            req, document_class=self.document_class
        )
        if self.config["reuse_cookies"]:
            for item in self.doc.cookies:
                self.cookies.set_cookie(item)
        self.doc.timestamp = now
        return self.doc

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
        self.config["cookies"] = {}
        self.cookies.clear()

    def __getstate__(self) -> dict[str, Any]:
        # TODO: should we use deep traversing?
        state = {}
        for cls in type(self).mro():
            cls_slots = getattr(cls, "__slots__", ())
            for slot_name in cls_slots:
                if hasattr(self, slot_name):
                    if slot_name == "cookies":
                        state["_cookies_items"] = list(self.cookies)
                    else:
                        state[slot_name] = getattr(self, slot_name)
        return state

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        # TODO: should we use deep traversing?
        # TODO: check assigned key is in slots
        for slot_name, value in state.items():
            if slot_name == "_cookies_items":
                jar = CookieJar()
                for item in value:
                    jar.set_cookie(item)
                self.cookies = jar
            else:
                setattr(self, slot_name, value)
