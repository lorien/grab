from __future__ import annotations

import os
import tempfile
from abc import ABCMeta, abstractmethod
from collections.abc import Generator, Mapping, MutableMapping
from contextlib import contextmanager
from http.cookiejar import CookieJar
from typing import Any, Optional, cast, overload

from grab.document import Document
from grab.request import Request


class BaseExtension(metaclass=ABCMeta):
    mount_points: list[str] = []

    __slots__ = ()

    def __set_name__(self, owner: BaseGrab, name: str) -> None:
        owner.extensions[name] = {
            "instance": self,
        }
        for point_name in self.mount_points:
            owner.mount_point_handlers[point_name].append(self)

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
    mount_point_handlers: MutableMapping[str, list[BaseExtension]] = {
        "request_cookies": [],
        "prepare_request_post": [],
        "response_post": [],
    }

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

    def setup_body_file(
        self,
        storage_dir: str,
        storage_filename: None | str,
        create_dir: bool = False,
    ) -> str:
        if create_dir and not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
        if storage_filename is None:
            file, file_path = tempfile.mkstemp(dir=storage_dir)
            os.close(file)
            return file_path
        return os.path.join(storage_dir, storage_filename)

    def detect_request_method(self, grab_config: Mapping[str, Any]) -> str:
        """Analyze request config and find which request method will be used.

        Returns request method in upper case
        """
        # pylint: disable=consider-alternative-union-syntax
        method = cast(Optional[str], grab_config["method"])
        # pylint: enable=consider-alternative-union-syntax
        if method:
            return method.upper()
        if grab_config["body"] or grab_config["fields"]:
            return "POST"
        return "GET"
