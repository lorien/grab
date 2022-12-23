from __future__ import annotations

import logging
import threading
from collections.abc import Mapping, MutableMapping
from copy import copy, deepcopy
from datetime import datetime
from secrets import SystemRandom
from typing import Any, cast
from urllib.parse import urljoin, urlsplit

from proxylist import ProxyList
from user_agent import generate_user_agent

from grab.base_transport import BaseTransport
from grab.cookie import CookieManager
from grab.document import Document
from grab.error import GrabError, GrabMisuseError, GrabTooManyRedirectsError
from grab.request import Request
from grab.transport import Urllib3Transport
from grab.types import GrabConfig
from grab.util.html import find_base_url
from grab.util.http import merge_with_dict

__all__ = ["Grab"]
MUTABLE_CONFIG_KEYS = ["fields", "headers", "cookies"]
logger = logging.getLogger("grab.base")
logger_network = logging.getLogger("grab.network")
system_random = SystemRandom()


def copy_config(config: GrabConfig) -> GrabConfig:
    """Copy grab config with correct handling of mutable config values."""
    cloned_config = copy(config)
    for key in MUTABLE_CONFIG_KEYS:
        cloned_config[key] = copy(config[key])
    return cloned_config


def default_config() -> GrabConfig:
    return {
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
        "document_type": "html",
        "body": None,
        "fields": None,
        "multipart": None,
        # Needs refactoring
        "redirect_limit": 10,  # -> Retry
        "follow_location": True,  # -> Redirect
        # Session Properties
        "common_headers": None,
        "reuse_cookies": True,
        "proxy_auto_change": True,
        "state": {},
    }


class Grab:
    __slots__ = (
        "proxylist",
        "config",
        "transport",
        "request_method",
        "cookies",
        "meta",
        "_doc",
    )
    document_class: type[Document] = Document
    # Attributes which should be processed when Grab instance is cloned
    clonable_attributes = ["proxylist"]

    def __init__(
        self,
        transport: None | BaseTransport | type[BaseTransport] = None,
        **kwargs: Any,
    ) -> None:
        self.transport = self.process_transport_option(transport, Urllib3Transport)
        self._doc: None | Document = None
        self.config: GrabConfig = default_config()
        self.config["common_headers"] = self.common_headers()
        self.cookies = CookieManager()
        self.proxylist = ProxyList.from_lines_list([])
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
        for key in self.clonable_attributes:
            setattr(grab, key, getattr(self, key))
        grab.cookies = deepcopy(self.cookies)
        if kwargs:
            grab.setup(**kwargs)
        return grab

    def dump_config(self) -> MutableMapping[str, Any]:
        """Make clone of current config."""
        conf = copy_config(self.config)
        conf["state"] = {
            "cookiejar_cookies": list(self.cookies.cookiejar),
        }
        return conf

    def load_config(self, config: GrabConfig) -> None:
        """Configure grab instance with external config object."""
        self.config = copy_config(config)
        if "cookiejar_cookies" in config["state"]:
            self.cookies = CookieManager.from_cookie_list(
                config["state"]["cookiejar_cookies"]
            )

    def setup(self, **kwargs: Any) -> None:
        """Set up Grab instance configuration."""
        for key in kwargs:
            if key not in self.config.keys():
                raise GrabMisuseError("Unknown option: %s" % key)

        if "url" in kwargs and self.config.get("url"):
            kwargs["url"] = self.make_url_absolute(kwargs["url"])
        self.config.update(kwargs)

    def prepare_request(self) -> Request:
        """Configure all things to make real network request.

        This method is called before doing real request via transport extension.
        """
        self.transport.reset()
        if self.config["url"] is None:
            raise GrabMisuseError("Request URL must be set")
        # TODO: activate
        # if self.config["method"] is None:
        #    raise GrabMisuseError("Request method must be set")
        # TODO: remove
        if not self.config["method"]:
            self.config["method"] = (
                "POST" if self.config["body"] or self.config["fields"] else "GET"
            )
        self.config["method"] = self.config["method"].upper()
        # proxylist extension
        if self.proxylist.size() and self.config["proxy_auto_change"]:
            self.change_proxy()
        # common headers extension
        if not self.config["headers"]:
            self.config["headers"] = {}
        if self.config["common_headers"]:
            merge_with_dict(self.config["headers"], self.config["common_headers"])
        # cookies extension
        req = self.create_request_from_config(self.config)
        self.sync_cookie_manager_with_request_cookies(req.cookies, req.url)
        return req

    def create_request_from_config(self, config: MutableMapping[str, Any]) -> Request:
        return Request(
            url=config["url"],
            encoding=config["encoding"],
            method=config["method"],
            timeout=config["timeout"],
            proxy=config["proxy"],
            proxy_type=config["proxy_type"],
            proxy_userpwd=config["proxy_userpwd"],
            headers=config["headers"],
            cookies=config["cookies"],
            body=config["body"],
            fields=config["fields"],
            multipart=config["multipart"],
            document_type=config["document_type"],
        )

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
                self.cookies.set(name=name, value=value, domain=request_host)

    def log_request(self, req: Request, extra: str = "") -> None:
        """Send request details to logging system."""
        thread_name = threading.current_thread().name.lower()
        proxy_info = (
            " via {} proxy of type {}{}".format(
                req.proxy,
                req.proxy_type,
                " with auth" if self.config["proxy_userpwd"] else "",
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
        if (
            self.config["follow_location"]
            and doc.code in {301, 302, 303, 307, 308}
            and doc.headers["Location"]
        ):
            return cast(str, doc.headers["Location"])
        return None

    def request(self, url: None | str = None, **kwargs: Any) -> Document:
        """Perform network request.

        You can specify grab settings in ``**kwargs``.
        Any keyword argument will be passed to ``self.config``.

        Returns: ``Document`` objects.
        """
        if url is not None:
            kwargs["url"] = url
        self.setup(**kwargs)
        req = self.prepare_request()
        redir_count = 0
        while True:
            self.log_request(req)
            try:
                self.transport.request(req, self.cookies)
            except GrabError:
                self.reset_temporary_options()
                raise
            else:
                with self.transport.wrap_transport_error():
                    doc = self.process_request_result(req)
                redir_url = self.find_redirect_url(doc)
                if redir_url is not None:
                    redir_count += 1
                    if redir_count > self.config["redirect_limit"]:
                        raise GrabTooManyRedirectsError()
                    self.setup(url=self.make_url_absolute(redir_url))
                    req = self.prepare_request()
                    continue
                return doc

    def submit(self, make_request: bool = True, **kwargs: Any) -> None | Document:
        """Submit current form.

        :param make_request: if `False` then grab instance will be
            configured with form post data but request will not be
            performed

        For details see `Document.submit()` method
        """
        assert self.doc is not None
        url, method, is_multipart, fields = self.doc.get_form_request(**kwargs)
        self.setup(
            url=url,
            method=method,
            fields=fields,
            multipart=is_multipart,
        )
        if make_request:
            return self.request()
        return None

    def process_request_result(self, req: Request) -> Document:
        """Process result of real request performed via transport extension."""
        now = datetime.utcnow()

        # It's important to delete old POST data after request is performed.
        # If POST data is not cleared then next request will try to use them
        # again!
        self.reset_temporary_options()
        self.doc = self.transport.prepare_response(
            req, document_class=self.document_class
        )
        if self.config["reuse_cookies"]:
            self.cookies.update(self.doc.cookies)
        self.doc.timestamp = now
        return self.doc

    def reset_temporary_options(self) -> None:
        self.config["body"] = None
        self.config["fields"] = None
        self.config["multipart"] = None
        self.config["method"] = None

    def change_proxy(self, random: bool = True) -> None:
        """Set random proxy from proxylist."""
        if self.proxylist.size():
            if random:
                proxy = self.proxylist.get_random_server()
            else:
                proxy = self.proxylist.get_next_server()
            if proxy.proxy_type is None:
                raise GrabMisuseError("Could not use proxy without defined proxy type")
            self.setup(
                proxy=proxy.get_address(),
                proxy_userpwd=proxy.get_userpwd(),
                proxy_type=proxy.proxy_type,
            )
        else:
            logger.debug("Proxy list is empty")

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

    def make_url_absolute(self, url: str, resolve_base: bool = False) -> str:
        """Make url absolute using previous request url as base url."""
        if self.config["url"]:
            if resolve_base and self.doc:
                ubody = self.doc.unicode_body()
                assert ubody is not None
                base_url = find_base_url(ubody)
                if base_url:
                    return urljoin(base_url, url)
            return urljoin(cast(str, self.config["url"]), url)
        return url

    def clear_cookies(self) -> None:
        """Clear all remembered cookies."""
        self.config["cookies"] = {}
        self.cookies.clear()

    def __getstate__(self) -> dict[str, Any]:
        """Reset cached lxml objects which could not be pickled."""
        state = {}
        for cls in type(self).mro():
            cls_slots = getattr(cls, "__slots__", ())
            for slot in cls_slots:
                if hasattr(self, slot):
                    state[slot] = getattr(self, slot)
        return state

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        for slot, value in state.items():
            setattr(self, slot, value)
