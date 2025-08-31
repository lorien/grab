from __future__ import annotations

import typing
from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Generator, Mapping, MutableMapping, Sequence
from contextlib import contextmanager
from copy import deepcopy
from typing import Any, Generic, TypeVar, cast

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
    ext_handlers: Mapping[str, Callable[..., Any]] = {}
    registry: MutableMapping[
        str,
        tuple[
            type[BaseClient[RequestT, ResponseT]],
            BaseExtension[RequestT, ResponseT],
        ],
    ] = {}
    __slots__ = ("owners",)

    def __set_name__(
        self, owner: type[BaseClient[RequestT, ResponseT]], attr: str
    ) -> None:
        self.registry[attr] = (owner, self)

    @abstractmethod
    def reset(self) -> None:
        ...

    @classmethod
    def get_extensions(
        cls, obj: BaseClient[RequestT, ResponseT]
    ) -> Sequence[tuple[str, BaseExtension[RequestT, ResponseT]]]:
        owner_reg: MutableMapping[
            type[BaseClient[RequestT, ResponseT]],
            list[tuple[str, BaseExtension[RequestT, ResponseT]]],
        ] = {}
        for ext_key, ext_tuple in cls.registry.items():
            owner_type, ext = ext_tuple
            owner_reg.setdefault(owner_type, []).append((ext_key, ext))
        ret = []
        stack = [obj.__class__]
        while stack:
            ptr = stack.pop()
            if ptr in owner_reg:
                ext_list = owner_reg[ptr]
                ret.extend(ext_list)
            for base in ptr.__bases__:
                if base != object().__class__:
                    stack.append(base)
        return ret


class Retry:
    def __init__(self) -> None:
        self.state: MutableMapping[str, int] = {}


class BaseClient(Generic[RequestT, ResponseT], metaclass=ABCMeta):
    __slots__ = ("transport", "ext_handlers")
    transport: BaseTransport[RequestT, ResponseT]

    @property
    @abstractmethod
    def request_class(self) -> type[RequestT]:
        ...

    @property
    @abstractmethod
    def default_transport_class(self) -> type[BaseTransport[RequestT, ResponseT]]:
        ...

    # extensions: MutableMapping[str, MutableMapping[str, Any]] = {}
    ext_handlers: Mapping[str, list[Callable[..., Any]]]

    def __init__(
        self,
        transport: None
        | BaseTransport[RequestT, ResponseT]
        | type[BaseTransport[RequestT, ResponseT]] = None,
    ) -> None:
        self.ext_handlers = {
            "request:pre": [],
            "request_cookies": [],
            "response:post": [],
            "init-retry": [],
            "retry": [],
        }
        for ext_key, _ext_proxy in BaseExtension.get_extensions(self):
            ext = getattr(self, ext_key)
            for point_name, func in ext.ext_handlers.items():
                self.ext_handlers[point_name].append(func)
        self.transport = self.default_transport_class.resolve_entity(
            transport, self.default_transport_class
        )
        for ext_key, _ext_proxy in BaseExtension.get_extensions(self):
            ext = getattr(self, ext_key)
            ext.reset()

    @abstractmethod
    def process_request_result(self, req: RequestT) -> ResponseT:
        ...

    def request(self, req: None | RequestT = None, **request_kwargs: Any) -> ResponseT:
        if req is None:
            req = self.request_class.create_from_mapping(request_kwargs)
        retry = Retry()
        all(x(retry) for x in self.ext_handlers["init-retry"])
        while True:
            all(func(req) for func in self.ext_handlers["request:pre"])
            self.transport.reset()
            self.transport.request(req)
            with self.transport.wrap_transport_error():
                doc = self.process_request_result(req)
            if any(
                (item := func(retry, req, doc)) != (None, None)
                for func in self.ext_handlers["retry"]
            ):
                # pylint: disable=deprecated-typing-alias
                retry, req = cast(typing.Tuple[Retry, RequestT], item)
                continue
            return doc

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
    def request(self, req: RequestT) -> None:  # pragma: no cover
        raise NotImplementedError

    @classmethod
    def resolve_entity(
        cls,
        entity: None
        | BaseTransport[RequestT, ResponseT]
        | type[BaseTransport[RequestT, ResponseT]],
        default: type[BaseTransport[RequestT, ResponseT]],
    ) -> BaseTransport[RequestT, ResponseT]:
        if entity and (
            not isinstance(entity, BaseTransport)
            and not issubclass(entity, BaseTransport)
        ):
            raise TypeError("Invalid BaseTransport entity: {}".format(entity))
        if entity is None:
            return default()
        if isinstance(entity, BaseTransport):
            return entity
        return entity()
