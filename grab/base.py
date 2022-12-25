from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Generator, Mapping, MutableMapping
from contextlib import contextmanager
from copy import deepcopy
from http.cookiejar import CookieJar
from typing import Any, Generic, TypeVar

__all__ = ["BaseRequest", "BaseExtension", "BaseClient", "BaseTransport"]

RequestT = TypeVar("RequestT", bound="BaseRequest")
ResponseT = TypeVar("ResponseT", bound="BaseResponse")
T = TypeVar("T")


class BaseRequest(metaclass=ABCMeta):
    init_keys: set[str] = set()

    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__,
            ", ".join("{}={!r}".format(*x) for x in self.__dict__.items()),
        )

    @classmethod
    def create_from_mapping(
        cls: type[RequestT], mapping: Mapping[str, Any]
    ) -> RequestT:
        for key in mapping:
            if key not in cls.init_keys:
                raise TypeError(
                    "Constructor of {} does not accept {} keyword parameter".format(
                        cls.__name__, key
                    )
                )
        return cls(**mapping)


class BaseResponse:
    pass


class BaseExtension(Generic[RequestT, ResponseT], metaclass=ABCMeta):
    extension_points: list[str] = []

    __slots__ = ()

    def __set_name__(self, owner: BaseClient[RequestT, ResponseT], attr: str) -> None:
        owner.extensions[attr] = {
            "instance": self,
        }
        for name in self.extension_points:
            owner.extension_point_handlers[name].append(self)

    def process_prepare_request_post(self, req: RequestT) -> None:
        pass

    def process_request_cookies(
        self, req: RequestT, jar: CookieJar  # pylint: disable=unused-argument
    ) -> None:
        pass

    def process_response_post(
        self, req: RequestT, doc: ResponseT  # pylint: disable=unused-argument
    ) -> None:
        pass

    @abstractmethod
    def reset(self) -> None:
        ...


class BaseClient(Generic[RequestT, ResponseT], metaclass=ABCMeta):
    __slots__ = ()

    extensions: MutableMapping[str, MutableMapping[str, Any]] = {}
    extension_point_handlers: MutableMapping[
        str, list[BaseExtension[RequestT, ResponseT]]
    ] = {
        "request_cookies": [],
        "prepare_request_post": [],
        "response_post": [],
    }

    def __init__(self) -> None:
        for item in self.extensions.values():
            item["instance"].reset()

    @abstractmethod
    def request(self, req: None | RequestT = None, **request_kwargs: Any) -> ResponseT:
        ...

    def clone(self: T) -> T:
        return deepcopy(self)


class BaseTransport(Generic[RequestT, ResponseT], metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    def reset(self) -> None:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    def prepare_response(
        self, req: RequestT, *, document_class: type[ResponseT]
    ) -> ResponseT:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    @contextmanager
    def wrap_transport_error(self) -> Generator[None, None, None]:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    def request(self, req: RequestT, cookiejar: CookieJar) -> None:  # pragma: no cover
        raise NotImplementedError
