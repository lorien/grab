from __future__ import annotations

import logging
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from typing import Any

from .base import BaseTransport
from .cloudscraper_transport import CloudscraperTransport
from .document import Document
from .errors import CloudflareProtectionDetectedError, GrabNetworkError
from .request import HttpRequest
from .transport import Urllib3Transport

LOG = logging.getLogger(__file__)

class SmartTransport(BaseTransport[HttpRequest, Document]):
    """Transport that automatically switches to cloudscraper when Cloudflare protection is detected."""

    def __init__(self, 
                cloudflare_bypass_enabled: bool = True,
                cloudflare_bypass_cache_timeout: int = 3600) -> None:
        super().__init__()
        self.regular_transport = Urllib3Transport()
        self._cf_transport: None | CloudscraperTransport = None
        self.cloudflare_bypass_enabled = cloudflare_bypass_enabled
        self.cloudflare_bypass_cache_timeout = cloudflare_bypass_cache_timeout
        # Track which domains need Cloudflare bypass
        self.cloudflare_domains: dict[str, float] = {}
        self._current_transport = self.regular_transport
        self._request: None | HttpRequest = None

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        # Regular transport and CF transport can't be pickled
        # We'll recreate them when unpickling
        state["regular_transport"] = None
        state["_cf_transport"] = None
        state["_current_transport"] = None
        state["_request"] = None
        return state

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        for slot, value in state.items():
            setattr(self, slot, value)
        self.regular_transport = Urllib3Transport()
        self._cf_transport = None
        self._current_transport = self.regular_transport

    def reset(self) -> None:
        """Reset the transport state."""
        self.regular_transport.reset()
        if self._cf_transport:
            self._cf_transport.reset()
        self._current_transport = self.regular_transport
        self._request = None

    @contextmanager
    def wrap_transport_error(self) -> Generator[None, None, None]:
        """Wrap transport errors and handle Cloudflare detection."""
        try:
            yield
        except CloudflareProtectionDetectedError as error:
            # If Cloudflare bypass is enabled, initialize Cloudflare transport
            if self.cloudflare_bypass_enabled:
                LOG.info("Cloudflare protection detected, switching to CloudscraperTransport")
                # Create CloudscraperTransport if not already created
                if self._cf_transport is None:
                    self._cf_transport = CloudscraperTransport()
                # Remember this domain needs Cloudflare bypass
                if self._request and self._request.url:
                    from urllib.parse import urlparse
                    domain = urlparse(self._request.url).netloc
                    import time
                    self.cloudflare_domains[domain] = time.time()
                # Try again with Cloudflare transport
                self._current_transport = self._cf_transport
                if self._request:
                    self._cf_transport.request(self._request)
                    return
            # If Cloudflare bypass is disabled or request is None, re-raise
            raise
        except GrabNetworkError:
            # Just re-raise other network errors
            raise

    def should_use_cloudflare_transport(self, req: HttpRequest) -> bool:
        """Determine if CloudscraperTransport should be used based on the domain history."""
        if not self.cloudflare_bypass_enabled or not req.url:
            return False
            
        from urllib.parse import urlparse
        domain = urlparse(req.url).netloc
        
        # Check if this domain is known to need Cloudflare bypass
        if domain in self.cloudflare_domains:
            # Check if cache entry is still valid
            import time
            if (time.time() - self.cloudflare_domains[domain]) < self.cloudflare_bypass_cache_timeout:
                return True
            # Cache expired, remove it
            del self.cloudflare_domains[domain]
        
        return False

    def request(self, req: HttpRequest) -> None:
        """Make a request, using the appropriate transport."""
        self._request = req
        
        # Determine which transport to use based on domain history
        if self.should_use_cloudflare_transport(req):
            LOG.debug("Using CloudscraperTransport for %s based on domain history", req.url)
            if self._cf_transport is None:
                self._cf_transport = CloudscraperTransport()
            self._current_transport = self._cf_transport
        else:
            self._current_transport = self.regular_transport
            
        # Make the request
        self._current_transport.request(req)

    def prepare_response(
        self, req: HttpRequest, *, document_class: type[Document] = Document
    ) -> Document:
        """Prepare the response from the current transport."""
        return self._current_transport.prepare_response(
            req, document_class=document_class
        )
