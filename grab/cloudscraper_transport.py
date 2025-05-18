from __future__ import annotations

import email.message
import logging
import time
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from http.client import HTTPResponse
from typing import Any, cast

import certifi
import cloudscraper
from cloudscraper.exceptions import CloudflareCaptchaError
from requests.exceptions import (
    ConnectionError,
    ReadTimeout,
    RequestException,
    SSLError,
    Timeout,
)

from .base import BaseTransport
from .document import Document
from .errors import (
    CloudflareProtectionDetectedError,
    GrabConnectionError,
    GrabInvalidResponseError,
    GrabTimeoutError,
)
from .request import HttpRequest
from .util.cookies import extract_response_cookies

LOG = logging.getLogger(__file__)


class CloudscraperTransport(BaseTransport[HttpRequest, Document]):
    """Grab network transport based on cloudscraper library for bypassing Cloudflare protection."""

    def __init__(self) -> None:
        super().__init__()
        self.scraper = cloudscraper.create_scraper()
        # Configure logging
        logger = logging.getLogger("cloudscraper")
        logger.setLevel(logging.WARNING)
        self._response = None
        self._connect_time: None | float = None
        self.reset()

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        # cloudscraper session cannot be pickled
        del state["scraper"]
        # Response object is also not good for pickling
        state["_response"] = None
        # Reset request object too
        state["_request"] = None
        return state

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        for slot, value in state.items():
            setattr(self, slot, value)
        self.scraper = cloudscraper.create_scraper()

    def reset(self) -> None:
        self._response = None
        self._connect_time = None

    @contextmanager
    def wrap_transport_error(self) -> Generator[None, None, None]:
        try:
            yield
        except ReadTimeout as ex:
            raise GrabTimeoutError("ReadTimeoutError", ex) from ex
        except Timeout as ex:
            raise GrabTimeoutError("TimeoutError", ex) from ex
        except ConnectionError as ex:
            raise GrabConnectionError("ConnectionError", ex) from ex
        except SSLError as ex:
            raise GrabConnectionError("SSLError", ex) from ex
        except CloudflareCaptchaError as ex:
            raise CloudflareProtectionDetectedError("CaptchaError", ex) from ex

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
        self.log_request(req)
        
        with self.wrap_transport_error():
            req_data = req.compile_request_data()
            proxies = None
            
            # Set up proxy if needed
            if req.proxy:
                proxy_auth = f"{req.proxy_userpwd}@" if req.proxy_userpwd else ""
                proxies = {
                    "http": f"{req.proxy_type}://{proxy_auth}{req.proxy}",
                    "https": f"{req.proxy_type}://{proxy_auth}{req.proxy}",
                }
            
            try:
                start_time = time.time()
                
                # Convert timeout to requests format
                timeout = (req.timeout.connect, req.timeout.read)
                
                # Make the request
                if req_data["method"].upper() == "GET":
                    res = self.scraper.get(
                        req_data["url"],
                        headers=req_data["headers"],
                        timeout=timeout,
                        proxies=proxies,
                        verify=certifi.where(),
                        allow_redirects=False,  # Grab handles redirects
                    )
                elif req_data["method"].upper() == "POST":
                    res = self.scraper.post(
                        req_data["url"],
                        data=req_data["body"],
                        headers=req_data["headers"],
                        timeout=timeout,
                        proxies=proxies,
                        verify=certifi.where(),
                        allow_redirects=False,  # Grab handles redirects
                    )
                else:
                    res = self.scraper.request(
                        req_data["method"],
                        req_data["url"],
                        data=req_data["body"],
                        headers=req_data["headers"],
                        timeout=timeout,
                        proxies=proxies,
                        verify=certifi.where(),
                        allow_redirects=False,  # Grab handles redirects
                    )
                
                self._connect_time = time.time() - start_time
                self._response = res
                
            except RequestException as ex:
                raise GrabInvalidResponseError(str(ex), ex) from ex

    def prepare_response(
        self, req: HttpRequest, *, document_class: type[Document] = Document
    ) -> Document:
        """Prepare response from cloudscraper Response object."""
        assert self._response is not None
        
        try:
            # Build head string from response headers
            head_str = ""
            for key, val in self._response.headers.items():
                head_str += f"{key}: {val}\r\n"
            head_str += "\r\n"
            head = head_str.encode("utf-8")
            
            # Get response body
            body = self._response.content
            
            # Convert headers to email.message.Message format
            hdr = email.message.Message()
            for key, val in self._response.headers.items():
                hdr[key] = val
                
            # Create Document
            return document_class(
                document_type=(
                    req.document_type if req.document_type is not None else "html"
                ),
                head=head,
                body=body,
                code=self._response.status_code,
                url=self._response.url,
                headers=hdr,
                encoding=req.encoding,
                cookies=extract_response_cookies(
                    req.url, req.headers, self._response.headers
                ),
            )
        finally:
            # Clean up resources
            self._response.close()
