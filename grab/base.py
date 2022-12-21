"""The core of grab package: the Grab class."""
from __future__ import annotations

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
from user_agent import generate_user_agent

from grab import error
from grab.base_transport import BaseTransport
from grab.cookie import CookieManager
from grab.document import Document
from grab.types import GrabConfig, TransportParam
from grab.util.html import find_base_url

__all__ = ("Grab",)
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
    return {
        # Request Properties
        "method": None,
        "url": None,
        "proxy": None,
        "proxy_type": None,
        "proxy_userpwd": None,
        "post": None,
        "multipart_post": None,
        "headers": {},
        "cookies": {},
        "timeout": 15,
        "connect_timeout": 3,
        "body_maxsize": None,
        "redirect_limit": 10,
        "encoding": None,
        # Not Clear Scope
        "document_type": "html",
        # Session Properties
        "cookiefile": None,
        "reuse_cookies": True,
        "common_headers": {},
        "follow_refresh": False,
        "follow_location": True,
        "proxy_auto_change": True,
        "state": {},
    }


class Grab:  # pylint: disable=too-many-instance-attributes, too-many-public-methods
    __slots__ = (
        "proxylist",
        "config",
        "transport",
        "transport_param",
        "request_method",
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
        transport: TransportParam = None,
        **kwargs: Any,
    ) -> None:
        self.meta: dict[str, Any] = {}
        self._doc: None | Document = None
        self.config: GrabConfig = default_config()
        self.config["common_headers"] = self.common_headers()
        self.cookies = CookieManager()
        self.proxylist = ProxyList.from_lines_list([])
        self.exception: None | Exception = None
        self.request_method: None | str = None
        self.transport_param: TransportParam = transport
        self.transport: None | BaseTransport = None
        self.reset()
        if kwargs:
            self.setup(**kwargs)

    @property
    def doc(self) -> None | Document:
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

        grab.doc = self.doc.copy() if self.doc else None

        for key in self.clonable_attributes:
            setattr(grab, key, getattr(self, key))
        grab.cookies = deepcopy(self.cookies)

        if kwargs:
            grab.setup(**kwargs)

        return grab

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

    def prepare_request(self, **kwargs: Any) -> None:
        """Configure all things to make real network request.

        This method is called before doing real request via
        transport extension.
        """
        if self.transport is None:
            self.setup_transport(self.transport_param)
        self.reset()
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
        proxy_info = (
            " via {} proxy of type {}{}".format(
                self.config["proxy"],
                self.config["proxy_type"],
                " with auth" if self.config["proxy_userpwd"] else "",
            )
            if self.config["proxy"]
            else ""
        )
        logger_network.debug(
            "%s%s%s %s%s",
            "" if (thread_name == "mainthread") else "[{}] ".format(thread_name),
            "[{}]".format(extra) if extra else "",
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
        if self.doc and self.config["follow_refresh"]:
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
                        url=self.make_url_absolute(redir_url),
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
        assert self.doc is not None
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

        if self.config["reuse_cookies"]:
            self.cookies.update(self.doc.cookies)

        self.doc.timestamp = now

        if self.config["cookiefile"]:
            self.cookies.save_to_file(self.config["cookiefile"])

        return self.doc

    def reset_temporary_options(self) -> None:
        self.config["post"] = None
        self.config["multipart_post"] = None
        self.config["method"] = None

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
                if slot != "__weakref__" and hasattr(self, slot):
                    state[slot] = getattr(self, slot)

        if state["_doc"]:
            state["_doc"].grab = weakref.proxy(self)

        return state

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        for slot, value in state.items():
            setattr(self, slot, value)
