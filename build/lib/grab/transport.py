from __future__ import annotations

import email.message
import logging
import ssl
import time
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from http.client import HTTPResponse
from pprint import pprint  # pylint: disable=unused-import
from typing import Any, cast

import certifi
from urllib3 import PoolManager, ProxyManager, exceptions, make_headers
from urllib3.contrib.socks import SOCKSProxyManager
from urllib3.exceptions import LocationParseError
from urllib3.response import HTTPResponse as Urllib3HTTPResponse
from urllib3.util.retry import Retry
from urllib3.util.timeout import Timeout

from .base import BaseTransport
from .document import Document
from .errors import GrabConnectionError, GrabInvalidResponseError, GrabTimeoutError
from .request import HttpRequest
from .util.cookies import extract_response_cookies

LOG = logging.getLogger(__file__)


class Urllib3Transport(BaseTransport[HttpRequest, Document]):
    """Grab network transport based on urllib3 library."""

    def __init__(self) -> None:
        super().__init__()
        self.pool = self.build_pool()
        # WTF: logging is configured here?
        logger = logging.getLogger("urllib3.connectionpool")
        logger.setLevel(logging.WARNING)
        self._response: None | Urllib3HTTPResponse = None
        self._connect_time: None | float = None
        self.reset()

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
        self._connect_time = None

    @contextmanager
    def wrap_transport_error(self) -> Generator[None, None, None]:
        try:
            yield
        except exceptions.ReadTimeoutError as ex:
            raise GrabTimeoutError("ReadTimeoutError", ex) from ex
        except exceptions.ConnectTimeoutError as ex:
            raise GrabConnectionError("ConnectTimeoutError", ex) from ex
        except exceptions.ProtocolError as ex:
            raise GrabConnectionError("ProtocolError", ex) from ex
        except exceptions.SSLError as ex:
            raise GrabConnectionError("SSLError", ex) from ex
        except ssl.SSLError as ex:
            raise GrabConnectionError("SSLError", ex) from ex

    def select_pool_for_request(
        self, req: HttpRequest
    ) -> PoolManager | ProxyManager | SOCKSProxyManager:
        if req.proxy:
            if req.proxy_userpwd:
                headers = make_headers(  # type: ignore
                    proxy_basic_auth=req.proxy_userpwd  # TODO: fix
                )
            else:
                headers = None
            proxy_url = "{}://{}".format(req.proxy_type, req.proxy)
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

    def log_request(self, req: HttpRequest) -> None:
        """Log request details via logging system."""
        proxy_info = (
            " via proxy {}://{}{}".format(
                req.proxy_type, req.proxy, " with auth" if req.proxy_userpwd else ""
            )
            if req.proxy
            else ""
        )
        LOG.debug("%s %s%s", req.method or "GET", req.url, proxy_info)

    def request(self, req: HttpRequest) -> None:
        pool: PoolManager | SOCKSProxyManager | ProxyManager = (
            self.select_pool_for_request(req)
        )
        self.log_request(req)
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
            timeout = Timeout(connect=req.timeout.connect, read=req.timeout.read)
            req_data = req.compile_request_data()
            try:
                start_time = time.time()
                res = pool.urlopen(  # type: ignore # TODO: fix
                    req_data["method"],
                    req_data["url"],
                    body=req_data["body"],
                    timeout=timeout,
                    retries=retry,
                    headers=req_data["headers"],
                    preload_content=False,
                )
                self._connect_time = time.time() - start_time
            except LocationParseError as ex:
                raise GrabInvalidResponseError(str(ex), ex) from ex

        self._response = res

    def read_with_timeout(self, req: HttpRequest) -> bytes:
        assert self._connect_time is not None
        assert self._response is not None
        chunks = []
        chunk_size = 10000
        bytes_read = 0
        op_started = time.time()
        while True:
            chunk = self._response.read(chunk_size)
            if chunk:
                bytes_read += len(chunk)
                chunks.append(chunk)
            else:
                break
            if (
                req.timeout.total
                and (time.time() - (op_started + self._connect_time))
                > req.timeout.total
            ):
                raise GrabTimeoutError
        return b"".join(chunks)

    def get_response_header_items(self) -> list[tuple[str, Any]]:
        """Return current response headers as items.

        This funciton is required to isolated smalles part of untyped code
        and hide it from mypy
        """
        headers = cast(HTTPResponse, self._response).headers
        return headers.items()

    def prepare_response(
        self, req: HttpRequest, *, document_class: type[Document] = Document
    ) -> Document:
        """Prepare response, duh.

        This methed is called after network request is completed
        hence the "self._request" is not None.

        Good to know: on python3 urllib3 headers are converted to str type
        using latin encoding.
        """
        assert self._response is not None
        try:
            head_str = ""
            # TODO: head must include first line like "GET / HTTP/1.1"
            for key, val in self.get_response_header_items():
                # WTF: is going here?
                new_key = key.encode("latin").decode("utf-8", errors="ignore")
                new_val = val.encode("latin").decode("utf-8", errors="ignore")
                head_str += "{}: {}\r\n".format(new_key, new_val)
            head_str += "\r\n"
            head = head_str.encode("utf-8")

            body = self.read_with_timeout(req)

            hdr = email.message.Message()
            for key, val in self.get_response_header_items():
                # WTF: is happening here?
                new_key = key.encode("latin").decode("utf-8", errors="ignore")
                new_val = val.encode("latin").decode("utf-8", errors="ignore")
                hdr[new_key] = new_val
            return document_class(
                document_type=(
                    req.document_type if req.document_type is not None else "html"
                ),
                head=head,
                body=body,
                code=self._response.status,
                url=(self._response.get_redirect_location() or req.url),
                headers=hdr,
                encoding=req.encoding,
                cookies=extract_response_cookies(
                    req.url, req.headers, self._response.headers
                ),
            )
        finally:
            self._response.release_conn()
