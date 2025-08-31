from __future__ import annotations

from typing import Any

from .base import BaseClient
from .document import Document
from .extensions import RedirectExtension
from .request import HttpRequest
from .transport import Urllib3Transport
from .util.types import resolve_entity

__all__ = ["HttpClient", "request"]


class HttpClient(BaseClient[HttpRequest, Document]):
    document_class: type[Document] = Document
    extension = RedirectExtension()
    request_class = HttpRequest
    default_transport_class = Urllib3Transport

    def request(
        self, req: None | str | HttpRequest = None, **request_kwargs: Any
    ) -> Document:
        if req is not None and not isinstance(req, HttpRequest):
            assert isinstance(req, str)
            request_kwargs["url"] = req
            req = None
        return super().request(req, **request_kwargs)

    def process_request_result(self, req: HttpRequest) -> Document:
        """Process result of real request performed via transport extension."""
        doc = self.transport.prepare_response(req, document_class=self.document_class)
        all(func(req, doc) for func in self.ext_handlers["response:post"])
        return doc


def request(
    url: None | str | HttpRequest = None,
    client: None | HttpClient | type[HttpClient] = None,
    **request_kwargs: Any,
) -> Document:
    client = resolve_entity(HttpClient, client, default=HttpClient)
    return client.request(url, **request_kwargs)
