from __future__ import annotations

import logging
from collections.abc import Mapping, MutableMapping
from copy import copy, deepcopy
from http.cookiejar import CookieJar
from pprint import pprint  # pylint: disable=unused-import
from secrets import SystemRandom
from typing import Any, cast, overload
from urllib.parse import urljoin

from .base import BaseGrab, BaseTransport
from .document import Document
from .errors import GrabMisuseError, GrabTooManyRedirectsError
from .request import Request
from .transport import Urllib3Transport
from .types import resolve_grab_entity, resolve_transport_entity

__all__ = ["Grab", "request"]
logger = logging.getLogger(__name__)
logger_network = logging.getLogger("grab.network")
system_random = SystemRandom()


def copy_config(config: Mapping[str, Any]) -> MutableMapping[str, Any]:
    """Copy grab config with correct handling of mutable config values."""
    return {x: copy(y) for x, y in config.items()}


def default_grab_config() -> MutableMapping[str, Any]:
    return {}


class Grab(BaseGrab):
    document_class: type[Document] = Document
    transport_class = Urllib3Transport

    def __init__(
        self,
        transport: None | BaseTransport | type[BaseTransport] = None,
        **kwargs: Any,
    ) -> None:
        self.config: MutableMapping[str, Any] = default_grab_config()
        self.transport = resolve_transport_entity(transport, self.transport_class)
        for item in self.extensions.values():
            item["instance"].reset()
        if kwargs:
            self.setup(**kwargs)

    def clone(self, **kwargs: Any) -> Grab:
        grab = deepcopy(self)
        # grab = Grab(transport=self.transport)
        # grab.config = copy_config(self.config)
        # # COOKIES EXTENSION
        # grab.cookies = self.cookies.clone()
        if kwargs:
            grab.setup(**kwargs)
        return grab

    def setup(self, **kwargs: Any) -> None:
        """Set up Grab instance configuration."""
        for key, val in kwargs.items():
            # COOKIES EXTENSION
            if key in self.config:
                self.config[key] = val
            else:
                raise GrabMisuseError("Unknown option: %s" % key)

    def prepare_request(self, request_config: MutableMapping[str, Any]) -> Request:
        """Configure all things to make real network request.

        This method is called before doing real request via transport extension.
        """
        self.transport.reset()
        cfg = copy(request_config)
        if cfg.get("url") is None:
            raise ValueError("Request could not be instantiated with no URL")
        if not cfg.get("method"):
            cfg["method"] = "GET"
        if cfg.get("follow_location") is None:
            cfg["follow_location"] = True
        req = Request.create_from_mapping(cfg)
        for ext in self.extension_point_handlers["prepare_request_post"]:
            ext.process_prepare_request_post(req)
        return req

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

    def get_request_cookies(self, req: Request) -> CookieJar:
        jar = CookieJar()
        for ext in self.extension_point_handlers["request_cookies"]:
            ext.process_request_cookies(req, jar)
        return jar

    @overload
    def request(self, url: Request, **request_kwargs: Any) -> Document:
        ...

    @overload
    def request(self, url: None | str = None, **request_kwargs: Any) -> Document:
        ...

    def request(
        self, url: None | str | Request = None, **request_kwargs: Any
    ) -> Document:
        if isinstance(url, Request):
            req = url
        else:
            if url is not None:
                request_kwargs["url"] = url
            req = self.prepare_request(request_kwargs)
        redir_count = 0
        while True:
            self.log_request(req)
            self.transport.request(req, self.get_request_cookies(req))
            with self.transport.wrap_transport_error():
                doc = self.process_request_result(req)
            if (
                req.follow_location
                and (redir_url := self.find_redirect_url(doc)) is not None
            ):
                redir_count += 1
                if redir_count > req.redirect_limit:
                    raise GrabTooManyRedirectsError()
                redir_url = urljoin(req.url, redir_url)
                request_kwargs["url"] = redir_url
                req = self.prepare_request(request_kwargs)
                continue
            return doc

    def submit(self, doc: Document, **kwargs: Any) -> Document:
        return self.request(Request(**doc.get_form_request(**kwargs)))

    def process_request_result(self, req: Request) -> Document:
        """Process result of real request performed via transport extension."""
        doc = self.transport.prepare_response(req, document_class=self.document_class)
        for ext in self.extension_point_handlers["response_post"]:
            ext.process_response_post(req, doc)
        return doc


def request(
    url: None | str | Request = None,
    grab: None | BaseGrab | type[BaseGrab] = None,
    **request_kwargs: Any,
) -> Document:
    grab = resolve_grab_entity(grab, default=Grab)
    return grab.request(url, **request_kwargs)
