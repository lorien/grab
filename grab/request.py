from __future__ import annotations

from typing import Any

from .util.timeout import Timeout

__all__ = ["Request"]


class Request:  # pylint: disable=too-many-instance-attributes
    def __init__(  # pylint: disable=too-many-arguments
        self,
        method: str,
        url: str,
        *,
        headers: None | dict[str, Any] = None,
        timeout: None | int | Timeout = None,
        cookies: None | dict[str, Any] = None,
        encoding: None | str = None,
        # proxy
        proxy_type: None | str = None,
        proxy: None | str = None,
        proxy_userpwd: None | str = None,
        # payload
        fields: Any = None,
        body: None | bytes = None,
        multipart: None | bool = None,
        document_type: None | str = None,
    ) -> None:
        self.encoding = encoding
        self.url = url
        if method not in {
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "HEAD",
            "CONNECT",
            "OPTIONS",
            "TRACE",
        }:
            raise ValueError("Method '{}' is not valid".format(method))
        self.method = method
        self.cookies = cookies or {}
        self.headers = headers or {}
        self.timeout: Timeout = self._process_timeout_param(timeout)
        # proxy
        self.proxy = proxy
        self.proxy_userpwd = proxy_userpwd
        self.proxy_type = proxy_type
        # payload
        self.body = body
        self.fields = fields
        self.multipart = multipart if multipart is not None else True
        self.document_type = document_type

    def get_full_url(self) -> str:
        return self.url

    def _process_timeout_param(self, value: None | float | Timeout) -> Timeout:
        if isinstance(value, Timeout):
            return value
        if value is None:
            return Timeout()
        return Timeout(total=float(value))
