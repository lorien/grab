from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Generator, Mapping, MutableMapping
from contextlib import contextmanager
from copy import deepcopy
from http.cookiejar import CookieJar
from typing import Any, Generic, Literal, TypeVar

__all__ = ["BaseRequest", "BaseExtension", "BaseClient", "BaseTransport"]

RequestT = TypeVar("RequestT", bound="BaseRequest")
ResponseT = TypeVar("ResponseT", bound="BaseResponse")
RequestDupT = TypeVar("RequestDupT", bound="BaseRequest")
ResponseDupT = TypeVar("ResponseDupT", bound="BaseResponse")
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
    ext_handlers: Mapping[
        Literal["request:pre"]
        | Literal["request_cookies"]
        | Literal["response:post"]
        | Literal["init-retry"]
        | Literal["retry"],
        Callable[..., Any],
    ] = {}

    __slots__ = ()

    def __set_name__(self, owner: BaseClient[RequestT, ResponseT], attr: str) -> None:
        owner.extensions[attr] = {
            "instance": self,
        }
        for point_name, func in self.ext_handlers.items():
            owner.ext_handlers[point_name].append(func)

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
    ext_handlers: Mapping[str, list[Callable[..., Any]]] = {
        "request:pre": [],
        "request_cookies": [],
        "response:post": [],
        "init-retry": [],
        "retry": [],
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
