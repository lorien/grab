from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Generator, MutableMapping
from contextlib import contextmanager
from copy import deepcopy
from http.cookiejar import CookieJar
from typing import Any, TypeVar, overload

from grab.document import Document
from grab.request import Request

T = TypeVar("T")


class BaseExtension(metaclass=ABCMeta):
    extension_points: list[str] = []

    __slots__ = ()

    def __set_name__(self, owner: BaseGrab, attr: str) -> None:
        owner.extensions[attr] = {
            "instance": self,
        }
        for name in self.extension_points:
            owner.extension_point_handlers[name].append(self)

    def process_prepare_request_post(self, req: Request) -> None:
        pass

    def process_request_cookies(
        self, req: Request, jar: CookieJar  # pylint: disable=unused-argument
    ) -> None:
        pass

    def process_response_post(
        self, req: Request, doc: Document  # pylint: disable=unused-argument
    ) -> None:
        pass

    @abstractmethod
    def reset(self) -> None:
        ...


class BaseGrab(metaclass=ABCMeta):
    __slots__ = ()

    extensions: MutableMapping[str, MutableMapping[str, Any]] = {}
    extension_point_handlers: MutableMapping[str, list[BaseExtension]] = {
        "request_cookies": [],
        "prepare_request_post": [],
        "response_post": [],
    }

    def __init__(self) -> None:
        for item in self.extensions.values():
            item["instance"].reset()

    @overload
    @abstractmethod
    def request(self, url: Request, **request_kwargs: Any) -> Document:
        ...

    @overload
    @abstractmethod
    def request(self, url: None | str = None, **request_kwargs: Any) -> Document:
        ...

    @abstractmethod
    def request(
        self, url: None | str | Request = None, **request_kwargs: Any
    ) -> Document:
        ...

    def clone(self: T) -> T:
        return deepcopy(self)


class BaseTransport(metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    def reset(self) -> None:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    def prepare_response(
        self, req: Request, *, document_class: type[Document] = Document
    ) -> Document:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    @contextmanager
    def wrap_transport_error(self) -> Generator[None, None, None]:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    def request(self, req: Request, cookiejar: CookieJar) -> None:  # pragma: no cover
        raise NotImplementedError
