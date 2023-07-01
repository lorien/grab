from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from copy import copy
from typing import Any, TypedDict
from urllib.parse import urlencode

from urllib3.filepost import encode_multipart_formdata

from .base import BaseRequest
from .util.structures import merge_with_dict
from .util.timeout import Timeout

__all__ = ["HttpRequest"]
URL_DATA_METHODS = {"DELETE", "GET", "HEAD", "OPTIONS"}
DEFAULT_REDIRECT_LIMIT = 20  # like in many web browsers
DEFAULT_PROCESS_REDIRECT = True
DEFAULT_METHOD = "GET"


class CompiledRequestData(TypedDict):
    method: str
    url: str
    headers: Mapping[str, Any]
    body: None | bytes


class HttpRequest(BaseRequest):  # pylint: disable=too-many-instance-attributes
    init_keys = {
        "method",
        "url",
        "headers",
        "timeout",
        "cookies",
        "encoding",
        "proxy",
        "proxy_type",
        "proxy_userpwd",
        "fields",
        "body",
        "multipart",
        "document_type",
        "redirect_limit",
        "process_redirect",
        "meta",
    }

    def __init__(  # noqa: PLR0913 pylint: disable=too-many-arguments,too-many-locals
        self,
        url: str,
        *,
        method: None | str = None,
        headers: None | MutableMapping[str, Any] = None,
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
        redirect_limit: None | int = None,
        process_redirect: None | bool = None,
        meta: None | Mapping[str, Any] = None,
    ) -> None:
        self.process_redirect = (
            process_redirect if process_redirect else DEFAULT_PROCESS_REDIRECT
        )
        self.redirect_limit = (
            redirect_limit if redirect_limit is not None else DEFAULT_REDIRECT_LIMIT
        )
        self.encoding = encoding
        if url is None:
            raise ValueError("URL must be set")
        self.url = url
        if method is None:
            method = DEFAULT_METHOD
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
        self.meta = meta or {}
        self.cookie_header: None | str = None

    def get_full_url(self) -> str:
        return self.url

    def _process_timeout_param(self, value: None | float | Timeout) -> Timeout:
        if isinstance(value, Timeout):
            return value
        if value is None:
            return Timeout()
        return Timeout(total=float(value))

    def compile_request_data(  # noqa: RUF100,CCR001
        self,
    ) -> CompiledRequestData:
        req_url = self.url
        req_hdr = copy(self.headers)
        req_body = None
        if self.method in URL_DATA_METHODS:
            if self.body:
                raise ValueError(
                    "Request.body could not be used with {} method".format(self.method)
                )
            if self.fields:
                req_url = req_url + "?" + urlencode(self.fields)
        else:
            if self.body:
                req_body = self.body
            if self.fields:
                if self.body:
                    raise ValueError(
                        "Request.body and Request.fields could not be set both"
                    )
                if self.multipart:
                    req_body, content_type = encode_multipart_formdata(self.fields)
                else:
                    req_body, content_type = (
                        urlencode(self.fields).encode(),
                        "application/x-www-form-urlencoded",
                    )
                req_hdr = merge_with_dict(
                    req_hdr,
                    {"Content-Type": content_type, "Content-Length": len(req_body)},
                    replace=True,
                )
        if self.cookie_header:
            req_hdr["Cookie"] = self.cookie_header
        return {
            "method": self.method,
            "url": req_url,
            "headers": req_hdr,
            "body": req_body,
        }
