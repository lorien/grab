from __future__ import annotations

from typing import Any

__all__ = ["Request"]


class Request:  # pylint: disable=too-many-instance-attributes
    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        url: str,
        method: str = "GET",
        headers: None | dict[str, Any] = None,
        timeout: int = 10,
        connect_timeout: int = 10,
        data: None | bytes = None,
        body_maxsize: None | int = None,
        proxy_type: None | str = None,
        proxy: None | str = None,
        proxy_userpwd: None | str = None,
    ) -> None:
        self.url = url
        self.method = method
        self.data = data
        self.proxy = proxy
        self.proxy_userpwd = proxy_userpwd
        self.proxy_type = proxy_type
        self.headers = headers or {}
        self.body_maxsize = body_maxsize
        self.timeout = timeout
        self.connect_timeout = connect_timeout
        # internal
        self.op_started: None | float = None

    def get_full_url(self) -> str:
        return self.url
