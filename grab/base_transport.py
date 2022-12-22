from __future__ import annotations

import os
import tempfile
from abc import abstractmethod
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from typing import Any, Optional, cast

from grab.cookie import CookieManager
from grab.document import Document
from grab.types import GrabConfig


class BaseTransport:
    @abstractmethod
    def reset(self) -> None:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    def prepare_response(
        self, grab_config: GrabConfig, *, document_class: type[Document] = Document
    ) -> Document:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    @contextmanager
    def wrap_transport_error(self) -> Generator[None, None, None]:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    def request(self) -> None:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    def process_config(
        self, grab_config: GrabConfig, grab_cookies: CookieManager
    ) -> None:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    def process_cookie_options(
        self,
        cookies: Mapping[str, Any],
        cookie_manager: CookieManager,
        request_url: str,
        request_headers: dict[str, Any],
    ) -> None | str:  # pragma: no cover
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
        if grab_config["post"] or grab_config["multipart_post"]:
            return "POST"
        return "GET"
