from __future__ import annotations

from typing import Any

from .util.timeout import Timeout

__all__ = ["Request"]


class Request:  # pylint: disable=too-many-instance-attributes
    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        url: str,
        method: str = "GET",
        headers: None | dict[str, Any] = None,
        timeout: None | int | Timeout = None,
        cookies: None | dict[str, Any] = None,
        encoding: None | str = None,
        # data: None | bytes = None,
        proxy_type: None | str = None,
        proxy: None | str = None,
        proxy_userpwd: None | str = None,
        post: Any = None,
        multipart_post: Any = None,
    ) -> None:
        self.encoding = encoding
        self.url = url
        self.method = method
        self.cookies = cookies or {}
        self.post = post
        self.multipart_post = multipart_post
        self.proxy = proxy
        self.proxy_userpwd = proxy_userpwd
        self.proxy_type = proxy_type
        self.headers = headers or {}
        self.timeout: Timeout = self._process_timeout_param(timeout)

    def get_full_url(self) -> str:
        return self.url

    def _process_timeout_param(self, value: None | float | Timeout) -> Timeout:
        if isinstance(value, Timeout):
            return value
        if value is None:
            return Timeout()
        return Timeout(total=float(value))
