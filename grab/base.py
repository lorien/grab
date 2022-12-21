"""The core of grab package: the Grab class."""
# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
from __future__ import annotations

import email.message
import itertools
import logging
import threading
import typing
import weakref
from collections.abc import Mapping, MutableMapping, Sequence
from contextlib import suppress
from copy import copy, deepcopy
from datetime import datetime
from secrets import SystemRandom
from typing import Any, cast
from urllib.parse import urljoin

from proxylist import ProxyList
from proxylist.parser import parse_proxy_line

from grab import error
from grab.base_transport import BaseTransport
from grab.cookie import CookieManager
from grab.document import Document
from grab.types import GrabConfig, TransportParam
from grab.util.html import find_base_url

__all__ = ("Grab",)
# This counter will used in enumerating network queries.
# Its value will be displayed in logging messages and also used
# in names of dumps
# I use mutable module variable to allow different
# instances of Grab to maintain single counter
# This could be helpful in debugging when your script
# creates multiple Grab instances - in case of shared counter
# grab instances do not overwrite dump logs
REQUEST_COUNTER = itertools.count(1)
MUTABLE_CONFIG_KEYS = ["post", "multipart_post", "headers", "cookies"]
TRANSPORT_CACHE: MutableMapping[tuple[str, str], type[BaseTransport]] = {}
TRANSPORT_ALIAS = {
    "urllib3": "grab.transport.Urllib3Transport",
}
DEFAULT_TRANSPORT = "urllib3"
logger = logging.getLogger("grab.base")
logger_network = logging.getLogger("grab.network")
system_random = SystemRandom()


def copy_config(
    config: GrabConfig, mutable_config_keys: None | Sequence[str] = None
) -> GrabConfig:
    """Copy grab config with correct handling of mutable config values."""
    cloned_config = copy(config)
    # Apply ``copy`` function to mutable config values
    for key in mutable_config_keys or MUTABLE_CONFIG_KEYS:
        cloned_config[key] = copy(config[key])
    return cloned_config


def default_config() -> GrabConfig:
    # TODO: Maybe config should be split into two entities:
    # 1) config which is not changed during request
    # 2) changeable settings
    return {
        # Common
        "url": None,
        # Debugging
        # Only for DEPRECATED transport
        "debug": False,
        "verbose_logging": False,
        # Only for selenium transport
        "webdriver": "firefox",
        "selenium_wait": 1,  # in seconds
        # Proxy
        "proxy": None,
        "proxy_type": None,
        "proxy_userpwd": None,
        "proxy_auto_change": True,
        # Method, Post
        "method": None,
        "post": None,
        "multipart_post": None,
        # Headers, User-Agent, Referer
        "headers": {},
        "common_headers": {},
        "user_agent": None,
        "user_agent_file": None,
        "referer": None,
        "reuse_referer": True,
        # Cookies
        "cookies": {},
        "reuse_cookies": True,
        "cookiefile": None,
        # Timeouts
        "timeout": 15,
        "connect_timeout": 3,
        # Connection
        "connection_reuse": True,
        # Response processing
        "nobody": False,
        "body_maxsize": None,
        "body_inmemory": True,
        "body_storage_dir": None,
        "body_storage_filename": None,
        "body_storage_create_dir": False,
        "reject_file_size": None,
        # Content compression
        "encoding": "gzip",
        # Network interface
        "interface": None,
        # DNS resolution
        "resolve": None,
        # Redirects
        "follow_refresh": False,
        "follow_location": True,
        "redirect_limit": 10,
        # Authentication
        "userpwd": None,
        # Character set to which any unicode data should be encoded
        # before get placed in request
        # This setting is overwritten after each request with
        # charset of retrieved document
        "charset": "utf-8",
        # Charset to use for converting content of response
        # into unicode, by default it is detected automatically
        "document_charset": None,
        # Content type control how DOM are built
        # For html type HTML DOM builder is used
        # For xml type XML DOM builder is used
        "content_type": "html",
        # Convert document body to lower case before building LXML tree
        # It does not affect `self.doc.body`
        "lowercased_tree": False,
        # Strip null bytes from document body before building lXML tree
        # It does not affect `self.doc.body`
        "strip_null_bytes": True,
        # Internal object to store
        "state": {},
    }


class Grab:  # pylint: disable=too-many-instance-attributes, too-many-public-methods
    __slots__ = (
        "proxylist",
        "config",
        "transport",
        "transport_param",
        "request_method",
        "request_counter",
        "__weakref__",
        "cookies",
        "meta",
        "exception",
        # Dirty hack to make it possible to inherit Grab from
        # multiple base classes with __slots__
        "_doc",
    )
    document_class: type[Document] = Document

    # Attributes which should be processed when clone
    # of Grab instance is creating
    clonable_attributes = ("proxylist",)

    # Complex config items which points to mutable objects
    mutable_config_keys = copy(MUTABLE_CONFIG_KEYS)

    #
    # Public methods
    #

    def __init__(
        self,
        document_body: None | bytes = None,
        transport: TransportParam = None,
        **kwargs: Any,
    ) -> None:
        """Create Grab instance."""
        self.meta: dict[str, Any] = {}
        self._doc: None | Document = None
        self.config: GrabConfig = default_config()
        self.config["common_headers"] = self.common_headers()
        self.cookies = CookieManager()
        self.proxylist = ProxyList.from_lines_list([])
        self.exception: None | Exception = None

        # makes pylint happy
        self.request_counter = 0
        self.request_method: None | str = None
        self.transport_param: TransportParam = transport
        self.transport: None | BaseTransport = None

        self.reset()
        if kwargs:
            self.setup(**kwargs)
        if document_body is not None:
            self.setup_document(document_body, charset=kwargs.get("document_charset"))

    @property
    def doc(self) -> Document:
        if self._doc is None:
            self._doc = Document(self.config)
        return self._doc

    @doc.setter
    def doc(self, obj: Document) -> None:
        self._doc = obj

    def setup_transport(
        self,
        transport_param: TransportParam,
        reset: bool = False,
    ) -> None:
        if self.transport is not None and not reset:
            raise error.GrabMisuseError(
                "Transport is already set up. Use"
                " setup_transport(..., reset=True) to explicitly setup"
                " new transport"
            )
        if transport_param is None:
            transport_param = DEFAULT_TRANSPORT
        if isinstance(transport_param, str):
            with suppress(KeyError):
                transport_param = TRANSPORT_ALIAS[transport_param]
            if "." not in transport_param:
                raise error.GrabMisuseError("Unknown transport: %s" % transport_param)
            mod_path, cls_name = transport_param.rsplit(".", 1)
            try:
                cls: type[BaseTransport] = TRANSPORT_CACHE[(mod_path, cls_name)]
            except KeyError:
                mod = __import__(mod_path, globals(), locals(), ["foo"])
                cls = getattr(mod, cls_name)
                TRANSPORT_CACHE[(mod_path, cls_name)] = cls
            self.transport_param = transport_param
            self.transport = cls()
        elif callable(transport_param):
            self.transport_param = transport_param
            self.transport = transport_param()
        else:
            raise error.GrabMisuseError(
                "Option `transport` should be string "
                "or class or callable. Got %s" % type(transport_param)
            )

    def reset(self) -> None:
        """Reset Grab instnce.

        Resets all attributes which could be modified during previous request
        or which is not initialized yet if this is the new Grab instance.

        This methods is automatically called before each network request.
        """
        self.request_method = None
        self.request_counter = 0
        self.exception = None
        if self.transport:
            self.transport.reset()

    def clone(self, **kwargs: Any) -> Grab:
        r"""Create clone of Grab instance.

        Cloned instance will have the same state: cookies, referrer, response
        document data

        :param \\**kwargs: overrides settings of cloned grab instance
        """
        grab = Grab(transport=self.transport_param)
        grab.config = self.dump_config()

        grab.doc = self.doc.copy()
        # grab.doc.grab = weakref.proxy(grab)

        for key in self.clonable_attributes:
            setattr(grab, key, getattr(self, key))
        grab.cookies = deepcopy(self.cookies)

        if kwargs:
            grab.setup(**kwargs)

        return grab

    def adopt(self, grab: Grab) -> None:
        """Copy the state of another `Grab` instance.

        WTF: this use case is needed for?
        Use case: create backup of current state to the cloned instance and
        then restore the state from it.
        """
        self.load_config(grab.config)

        self.doc = grab.doc.copy(new_grab_config=self.config)

        for key in self.clonable_attributes:
            setattr(self, key, getattr(grab, key))
        self.cookies = deepcopy(grab.cookies)

    def dump_config(self) -> dict[str, Any]:
        """Make clone of current config."""
        conf = cast(
            # pylint: disable=deprecated-typing-alias
            typing.Dict[str, Any],
            copy_config(self.config, self.mutable_config_keys)
            # pylint: enable=deprecated-typing-alias
        )
        conf["state"] = {
            "cookiejar_cookies": list(self.cookies.cookiejar),
        }
        return conf

    def load_config(self, config: GrabConfig) -> None:
        """Configure grab instance with external config object."""
        self.config = copy_config(config, self.mutable_config_keys)
        if "cookiejar_cookies" in config["state"]:
            self.cookies = CookieManager.from_cookie_list(
                config["state"]["cookiejar_cookies"]
            )

    def setup(self, **kwargs: Any) -> None:
        """Set up Grab instance configuration."""
        for key in kwargs:
            if key not in self.config.keys():
                raise error.GrabMisuseError("Unknown option: %s" % key)

        if "url" in kwargs and self.config.get("url"):
            kwargs["url"] = self.make_url_absolute(kwargs["url"])
        self.config.update(kwargs)

    def go(self, url: str, **kwargs: Any) -> Document:  # pylint: disable=invalid-name
        """Go to ``url``.

        Args:
            :url: could be absolute or relative. If relative then t will be
                appended to the absolute URL of previous request.
        """
        return self.request(url=url, **kwargs)

    def download(self, url: str, location: str, **kwargs: Any) -> int:
        """Fetch document located at ``url`` and save to to ``location``."""
        doc = self.go(url, **kwargs)
        assert doc.body is not None
        with open(location, "wb") as out:
            out.write(doc.body)
        return len(doc.body)

    def prepare_request(self, **kwargs: Any) -> None:
        """Configure all things to make real network request.

        This method is called before doing real request via
        transport extension.
        """
        if self.transport is None:
            self.setup_transport(self.transport_param)
        self.reset()
        self.request_counter = next(REQUEST_COUNTER)
        if kwargs:
            self.setup(**kwargs)
        if self.proxylist.size() and self.config["proxy_auto_change"]:
            self.change_proxy()
        self.request_method = cast(BaseTransport, self.transport).detect_request_method(
            self.config
        )
        cast(BaseTransport, self.transport).process_config(self.config, self.cookies)

    def log_request(self, extra: str = "") -> None:
        """Send request details to logging system."""
        thread_name = threading.current_thread().name.lower()
        thread_name = "" if (thread_name == "mainthread") else "-%s" % thread_name

        if self.config["proxy"]:
            if self.config["proxy_userpwd"]:
                auth = " with authorization"
            else:
                auth = ""
            proxy_info = " via %s proxy of type %s%s" % (
                self.config["proxy"],
                self.config["proxy_type"],
                auth,
            )
        else:
            proxy_info = ""
        if extra:
            extra = "[%s] " % extra
        logger_network.debug(
            "[%s%s] %s%s %s%s",
            ("%02d" % self.request_counter),
            thread_name,
            extra,
            self.request_method or "GET",
            self.config["url"],
            proxy_info,
        )

    def find_redirect_url(self, doc: Document) -> tuple[None | str, None | str]:
        assert doc.headers is not None
        if (
            self.config["follow_location"]
            and doc.code in {301, 302, 303, 307, 308}
            and doc.headers["Location"]
        ):
            return doc.headers["Location"], "location"
        if self.config["follow_refresh"]:
            url = self.doc.get_meta_refresh_url()
            if url is not None:
                return url, "refresh"
        return None, None

    def request(self, **kwargs: Any) -> Document:
        """Perform network request.

        You can specify grab settings in ``**kwargs``.
        Any keyword argument will be passed to ``self.config``.

        Returns: ``Document`` objects.
        """
        self.prepare_request(**kwargs)
        refresh_count = 0

        while True:
            self.log_request()

            try:
                cast(BaseTransport, self.transport).request()
            except error.GrabError as ex:
                self.exception = ex
                self.reset_temporary_options()
                raise
            else:
                with cast(BaseTransport, self.transport).wrap_transport_error():
                    doc = self.process_request_result()
                redir_url, _ = self.find_redirect_url(doc)
                if redir_url is not None:
                    refresh_count += 1
                    if refresh_count > self.config["redirect_limit"]:
                        raise error.GrabTooManyRedirectsError()
                    self.prepare_request(
                        url=self.make_url_absolute(redir_url), referer=None
                    )
                    continue
                return doc

    def submit(self, make_request: bool = True, **kwargs: Any) -> None | Document:
        """Submit current form.

        :param make_request: if `False` then grab instance will be
            configured with form post data but request will not be
            performed

        For details see `Document.submit()` method

        Example::

            # Assume that we going to some page with some form
            g.go('some url')
            # Fill some fields
            g.doc.set_input('username', 'bob')
            g.doc.set_input('pwd', '123')
            # Submit the form
            g.submit()

            # or we can just fill the form
            # and do manual submission
            g.doc.set_input('foo', 'bar')
            g.submit(make_request=False)
            g.request()

            # for multipart forms we can specify files
            from grab import UploadFile
            g.doc.set_input('img', UploadFile('/path/to/image.png'))
            g.submit()
        """
        result = self.doc.get_form_request(**kwargs)
        if result["multipart_post"]:
            self.setup(multipart_post=result["multipart_post"])
        if result["post"]:
            self.setup(post=result["post"])
        if result["url"]:
            self.setup(url=result["url"])
        if make_request:
            return self.request()
        return None

    def process_request_result(self) -> Document:
        """Process result of real request performed via transport extension."""
        now = datetime.utcnow()

        # It's important to delete old POST data after request is performed.
        # If POST data is not cleared then next request will try to use them
        # again!
        self.reset_temporary_options()

        self.doc = cast(BaseTransport, self.transport).prepare_response(
            self.config, document_class=self.document_class
        )

        self.doc.process_grab_config(self.config)

        if self.config["reuse_cookies"]:
            self.cookies.update(self.doc.cookies)

        self.doc.timestamp = now

        self.config["charset"] = self.doc.charset

        if self.config["cookiefile"]:
            self.cookies.save_to_file(self.config["cookiefile"])

        if self.config["reuse_referer"]:
            self.config["referer"] = self.doc.url

        return self.doc

    def reset_temporary_options(self) -> None:
        self.config["post"] = None
        self.config["multipart_post"] = None
        self.config["method"] = None
        self.config["body_storage_filename"] = None

    def setup_document(self, content: bytes, **kwargs: Any) -> None:
        """Set up `response` object without real network requests.

        Useful for testing and debugging.

        All ``**kwargs`` will be passed to `Document` constructor.
        """
        self.reset()
        if isinstance(content, str):
            raise error.GrabMisuseError(
                "Method `setup_document` accepts only "
                "byte string in `content` argument."
            )

        # Configure Document instance
        doc = self.document_class(self.config)

        # DOCUMENT ARGS:
        # body, head, status, headers, charset, code, url
        doc.body = content
        doc.head = b"HTTP/1.1 200 OK\r\n\r\n"
        doc.status = ""
        doc.headers = email.message.Message()
        doc.setup_charset(kwargs.get("charset"))
        doc.code = 200
        doc.url = ""

        # WTF: WHat the hell it means?
        for key, value in kwargs.items():
            # if key and value is None:
            #    value = "utf-8"
            setattr(doc, key, "utf-8" if (key and value is None) else value)

        self.doc = doc

    def change_proxy(self, random: bool = True) -> None:
        """Set random proxy from proxylist."""
        if self.proxylist.size():
            if random:
                proxy = self.proxylist.get_random_server()
            else:
                proxy = self.proxylist.get_next_server()
            if proxy.proxy_type is None:
                raise error.GrabMisuseError(
                    "Could not use proxy without defined proxy type"
                )
            self.setup(
                proxy=proxy.get_address(),
                proxy_userpwd=proxy.get_userpwd(),
                proxy_type=proxy.proxy_type,
            )
        else:
            logger.debug("Proxy list is empty")

    #
    # Private methods
    #

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
        }

    def make_url_absolute(self, url: str, resolve_base: bool = False) -> str:
        """Make url absolute using previous request url as base url."""
        if self.config["url"]:
            if resolve_base:
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

    def setup_with_proxyline(self, line: str, proxy_type: str = "http") -> None:
        host, port, user, pwd = parse_proxy_line(line)
        server_port = "%s:%s" % (host, port)
        self.setup(proxy=server_port, proxy_type=proxy_type)
        if user:
            userpwd = "%s:%s" % (user, pwd)
            self.setup(proxy_userpwd=userpwd)

    def __getstate__(self) -> dict[str, Any]:
        """Reset cached lxml objects which could not be pickled."""
        state = {}
        for cls in type(self).mro():
            cls_slots = getattr(cls, "__slots__", ())
            for slot in cls_slots:
                if slot != "__weakref__" and hasattr(self, slot):
                    state[slot] = getattr(self, slot)

        if state["_doc"]:
            state["_doc"].grab = weakref.proxy(self)

        return state

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        for slot, value in state.items():
            setattr(self, slot, value)


# For backward compatibility
# WTF???
BaseGrab = Grab
