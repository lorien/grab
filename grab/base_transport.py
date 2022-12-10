from __future__ import annotations

import os
import tempfile
from abc import abstractmethod
from contextlib import contextmanager
from typing import Any, Generator, Mapping, Optional, cast

from grab.cookie import CookieManager
from grab.document import Document
from grab.types import GrabConfig


class BaseTransport:
    def reset(self) -> None:
        pass

    @abstractmethod
    def prepare_response(self, grab_config: GrabConfig) -> Document:
        raise NotImplementedError

    @abstractmethod
    @contextmanager
    def wrap_transport_error(self) -> Generator[None, None, None]:
        raise NotImplementedError

    @abstractmethod
    def request(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def process_config(
        self, grab_config: GrabConfig, grab_cookies: CookieManager
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def process_cookie_options(
        self,
        grab_config: GrabConfig,
        cookie_manager: CookieManager,
        request_url: str,
        request_headers: dict[str, Any],
    ) -> Optional[str]:
        raise NotImplementedError

    def setup_body_file(
        self,
        storage_dir: str,
        storage_filename: Optional[str],
        create_dir: bool = False,
    ) -> str:
        if create_dir and not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
        if storage_filename is None:
            file, file_path = tempfile.mkstemp(dir=storage_dir)
            os.close(file)
        else:
            file_path = os.path.join(storage_dir, storage_filename)
        return file_path  # noqa: R504

    def detect_request_method(self, grab_config: Mapping[str, Any]) -> str:
        """
        Analyze request config and find which request method will be used.

        Returns request method in upper case
        """
        method = cast(Optional[str], grab_config["method"])
        if method:
            method = method.upper()
        else:
            if grab_config["post"] or grab_config["multipart_post"]:
                method = "POST"
            else:
                method = "GET"
        return method  # noqa: R504
