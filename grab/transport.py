from __future__ import annotations

import email.message
import logging
import ssl
import time
import urllib.request
from collections.abc import Generator, Mapping, MutableMapping, Sequence
from contextlib import contextmanager
from copy import copy
from http.client import HTTPResponse
from http.cookiejar import CookieJar
from pprint import pprint  # pylint: disable=unused-import
from typing import Any, cast
from urllib.parse import urlsplit

import certifi
from urllib3 import PoolManager, ProxyManager, exceptions, make_headers
from urllib3.contrib.socks import SOCKSProxyManager
from urllib3.exceptions import LocationParseError
from urllib3.fields import RequestField
from urllib3.filepost import encode_multipart_formdata

# from urllib3.fields import RequestField
# from urllib3.filepost import encode_multipart_formdata
from urllib3.response import HTTPResponse as Urllib3HTTPResponse
from urllib3.util.retry import Retry
from urllib3.util.timeout import Timeout

from grab import error
from grab.cookie import CookieManager, MockRequest, MockResponse
from grab.document import Document
from grab.error import GrabMisuseError, GrabTimeoutError
from grab.request import Request
from grab.types import GrabConfig
from grab.upload import UploadContent, UploadFile
from grab.util.http import normalize_http_values, normalize_post_data, normalize_url

from .base_transport import BaseTransport


def assemble(
    req: Request, cookie_manager: CookieManager
) -> tuple[dict[str, Any], bytes | None]:
    req_hdr = copy(req.headers)
    post_headers, req_data = process_config_post(
        req.post,
        req.multipart_post,
        req.method,
        req.encoding or "utf-8",
    )
    req_hdr.update(post_headers)

    cookie_hdr = cookie_manager.get_cookie_header(req.url, req_hdr)
    if cookie_hdr:
        req_hdr["Cookie"] = cookie_hdr

    return req_hdr, req_data


def process_upload_items(
    items: Sequence[tuple[str, Any]]
) -> Sequence[RequestField | tuple[str, Any]]:
    result: list[RequestField | tuple[str, Any]] = []
    for key, val in items:
        if isinstance(val, UploadContent):
            headers = {"Content-Type": val.content_type}
            field = RequestField(
                name=key, data=val.content, filename=val.filename, headers=headers
            )
            field.make_multipart(content_type=val.content_type)
            result.append(field)
        elif isinstance(val, UploadFile):
            with open(val.path, "rb") as inp:
                data = inp.read()
            headers = {"Content-Type": val.content_type}
            field = RequestField(
                name=key, data=data, filename=val.filename, headers=headers
            )
            field.make_multipart(content_type=val.content_type)
            result.append(field)
        else:
            result.append((key, val))
    return result


def process_config_post(
    post: Any, multipart_post: Any, method: str, encoding: str
) -> tuple[dict[str, Any], None | bytes]:
    if method in {"POST", "PUT"} and (post is None and multipart_post is None):
        raise GrabMisuseError(
            "Neither `post` or `multipart_post`"
            " options was specified for the %s"
            " request" % method
        )
    extra_headers = {}
    post_data: None | bytes = None
    if multipart_post is not None:
        post_data = multipart_post
        if isinstance(post_data, str):
            raise GrabMisuseError("Option multipart_post data does not accept unicode.")
        if isinstance(post_data, bytes):
            pass
        else:
            # WTF: why I encode things into bytes and then decode them back?
            post_items: Sequence[tuple[bytes, Any]] = normalize_http_values(
                multipart_post,
                encoding=encoding,
            )
            post_items2: Sequence[tuple[str, Any]] = [
                (
                    x[0].decode(encoding) if isinstance(x[0], bytes) else x[0],
                    x[1].decode(encoding) if isinstance(x[1], bytes) else x[1],
                )
                for x in post_items
            ]
            post_items3 = process_upload_items(post_items2)
            post_data, content_type = encode_multipart_formdata(
                post_items3
            )  # type: ignore # FIXME
            extra_headers["Content-Type"] = content_type
        extra_headers["Content-Length"] = len(post_data)
    elif post is not None:
        post_data = normalize_post_data(post, encoding)
        extra_headers["Content-Length"] = len(post_data)
    return extra_headers, post_data


def update_cookie_manager(
    cookie_manager: CookieManager,
    cookies: Mapping[str, Any],
    request_url: str,
) -> None:
    request_host = urlsplit(request_url).hostname
    if request_host and cookies:
        if request_host.startswith("www."):
            request_host_no_www = request_host[4:]
        else:
            request_host_no_www = request_host

        # Process `cookies` option that is simple dict i.e.
        # it provides only `name` and `value` attributes of cookie
        # No domain, no path, no expires, etc
        # To put these cookies into cookie manager we need to
        # provide the domain of current request url
        # Trying to guess better domain name by removing leading "www."
        for name, value in cookies.items():
            cookie_manager.set(name=name, value=value, domain=request_host_no_www)


class Urllib3Transport(BaseTransport):
    """Grab network transport based on urllib3 library."""

    def __init__(self) -> None:
        super().__init__()
        self.pool = self.build_pool()
        # WTF: logging is configured here?
        logger = logging.getLogger("urllib3.connectionpool")
        logger.setLevel(logging.WARNING)
        self._request: None | Request = None
        self._response: None | Urllib3HTTPResponse = None
        self._request_item: tuple[dict[str, Any], bytes | None] = {}, None

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        # PoolManager could not be pickled
        del state["pool"]
        # urllib3.HTTPReponse is also not good for pickling
        state["_response"] = None
        # let's reset request object too
        state["_request"] = None
        return state

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        for slot, value in state.items():
            setattr(self, slot, value)
        self.pool = self.build_pool()

    def build_pool(self) -> PoolManager:
        # http://urllib3.readthedocs.io/en/latest/user-guide.html#certificate-verification
        return PoolManager(10, cert_reqs="CERT_REQUIRED", ca_certs=certifi.where())

    def reset(self) -> None:
        self._response = None
        self._request = None
        self._request_item = {}, None

    def process_config(
        self, grab_config: MutableMapping[str, Any], grab_cookies: CookieManager
    ) -> None:
        if not isinstance(grab_config["cookies"], dict):
            raise error.GrabMisuseError("cookies option should be a dict")
        try:
            request_url = normalize_url(grab_config["url"])
        except Exception as ex:
            raise error.GrabInvalidUrl("%s: %s" % (str(ex), str(grab_config["url"])))
        method = self.detect_request_method(grab_config)
        # HEADERS
        req_headers: dict[str, str] = copy(grab_config["common_headers"])
        if grab_config["headers"]:
            req_headers.update(grab_config["headers"])

        self._request = Request(
            url=request_url,
            encoding=grab_config["encoding"],
            method=method,
            body_maxsize=grab_config["body_maxsize"],
            timeout=grab_config["timeout"],
            connect_timeout=grab_config["connect_timeout"],
            proxy=grab_config["proxy"],
            proxy_type=grab_config["proxy_type"],
            proxy_userpwd=grab_config["proxy_userpwd"],
            headers=req_headers,
            cookies=grab_config["cookies"],
            # data=req_data,
            post=grab_config["post"],
            multipart_post=grab_config["multipart_post"],
        )
        update_cookie_manager(grab_cookies, self._request.cookies, self._request.url)
        self._request_item = assemble(self._request, grab_cookies)

    @contextmanager
    def wrap_transport_error(self) -> Generator[None, None, None]:
        try:
            yield
        except exceptions.ReadTimeoutError as ex:
            raise error.GrabTimeoutError("ReadTimeoutError", ex)
        except exceptions.ConnectTimeoutError as ex:
            raise error.GrabConnectionError("ConnectTimeoutError", ex)
        except exceptions.ProtocolError as ex:
            raise error.GrabConnectionError("ProtocolError", ex)
        except exceptions.SSLError as ex:
            raise error.GrabConnectionError("SSLError", ex)
        except ssl.SSLError as ex:
            raise error.GrabConnectionError("SSLError", ex)

    def select_pool_for_request(
        self, req: Request
    ) -> PoolManager | ProxyManager | SOCKSProxyManager:
        if req.proxy:
            if req.proxy_userpwd:
                headers = make_headers(
                    proxy_basic_auth=req.proxy_userpwd
                )  # type: ignore # FIXME
            else:
                headers = None
            proxy_url = "%s://%s" % (req.proxy_type, req.proxy)
            if req.proxy_type == "socks5":
                return SOCKSProxyManager(
                    proxy_url, cert_reqs="CERT_REQUIRED", ca_certs=certifi.where()
                )  # , proxy_headers=headers)
            return ProxyManager(
                proxy_url,
                proxy_headers=headers,
                cert_reqs="CERT_REQUIRED",
                ca_certs=certifi.where(),
            )
        return self.pool

    def request(self) -> None:
        req = cast(Request, self._request)

        pool: PoolManager | SOCKSProxyManager | ProxyManager = (
            self.select_pool_for_request(req)
        )
        with self.wrap_transport_error():
            # Retries can be disabled by passing False:
            # http://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html#module-urllib3.util.retry
            # Do not use False because of warning:
            # Converted retries value: False -> Retry(total=False,
            # connect=None, read=None, redirect=0, status=None)
            retry = Retry(
                total=False,
                connect=False,
                read=False,
                redirect=0,
                status=None,
            )
            # The read timeout is not total response time timeout
            # It is the timeout on read of next data chunk from the server
            # Total response timeout is handled by Grab
            timeout = Timeout(connect=req.connect_timeout, read=req.timeout)
            req_url = req.url
            req_method = req.method
            req.op_started = time.time()
            req_hdr, req_data = self._request_item
            try:
                res = pool.urlopen(  # type: ignore # FIXME
                    req_method,
                    req_url,
                    body=req_data,
                    timeout=timeout,
                    retries=retry,
                    headers=req_hdr,
                    preload_content=False,
                )
            except LocationParseError as ex:
                raise error.GrabInvalidResponse(str(ex), ex)

        self._response = res

    def read_with_timeout(self) -> bytes:
        maxsize = cast(Request, self._request).body_maxsize
        if isinstance(maxsize, int) and not maxsize:
            return b""
        chunks = []
        default_chunk_size = 10000
        chunk_size = (
            min(default_chunk_size, maxsize + 1) if maxsize else default_chunk_size
        )
        bytes_read = 0
        while True:
            chunk = cast(HTTPResponse, self._response).read(chunk_size)
            if chunk:
                bytes_read += len(chunk)
                chunks.append(chunk)
                if maxsize and bytes_read > maxsize:
                    # reached limit on bytes to read
                    break
            else:
                break
            if cast(Request, self._request).timeout and (
                time.time() - cast(float, cast(Request, self._request).op_started)
                > cast(float, cast(Request, self._request).timeout)
            ):
                raise GrabTimeoutError
        data = b"".join(chunks)
        if maxsize:
            return data[:maxsize]
        return data

    def get_response_header_items(self) -> list[tuple[str, Any]]:
        """Return current response headers as items.

        This funciton is required to isolated smalles part of untyped code
        and hide it from mypy
        """
        headers = cast(HTTPResponse, self._response).headers
        return headers.items()

    def prepare_response(
        self, grab_config: GrabConfig, *, document_class: type[Document] = Document
    ) -> Document:
        """Prepare response, duh.

        This methed is called after network request is completed
        hence the "self._request" is not None.

        Good to know: on python3 urllib3 headers are converted to str type
        using latin encoding.
        """
        if not self._response:
            raise GrabMisuseError(
                "Method prepare response must be callled only"
                " after network response is received"
            )
        try:

            head_str = ""
            # FIXME: head must include first line like "GET / HTTP/1.1"
            for key, val in self.get_response_header_items():
                # WTF: is going here?
                new_key = key.encode("latin").decode("utf-8", errors="ignore")
                new_val = val.encode("latin").decode("utf-8", errors="ignore")
                head_str += "%s: %s\r\n" % (new_key, new_val)
            head_str += "\r\n"
            head = head_str.encode("utf-8")

            body = self.read_with_timeout()

            hdr = email.message.Message()
            for key, val in self.get_response_header_items():
                # WTF: is happening here?
                new_key = key.encode("latin").decode("utf-8", errors="ignore")
                new_val = val.encode("latin").decode("utf-8", errors="ignore")
                hdr[new_key] = new_val
            jar = self.extract_cookiejar()  # self._response, self._request)
            return document_class(
                document_type=grab_config["document_type"],
                head=head,
                body=body,
                code=self._response.status,
                url=(
                    self._response.get_redirect_location()
                    or cast(Request, self._request).url
                ),
                headers=hdr,
                encoding=grab_config["encoding"],
                cookies=jar,
            )
        finally:
            self._response.release_conn()

    def extract_cookiejar(self) -> CookieJar:
        jar = CookieJar()
        # self._respose could be None
        # if this method is called from custom prepare response
        if self._response and self._request:
            jar.extract_cookies(
                cast(
                    HTTPResponse,
                    MockResponse(self._response.headers),
                ),
                cast(
                    urllib.request.Request,
                    MockRequest(self._request.url, self._request.headers),
                ),
            )
        return jar
