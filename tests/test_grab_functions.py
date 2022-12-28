from typing import Any
from unittest import TestCase

from grab import HttpClient, request
from grab.document import Document


class RequestFuncTestCase(TestCase):
    def test_request_custom_grab(self) -> None:
        class DummyDocument(Document):
            pass

        class DummyHttpClient(HttpClient):
            def request(self, *_args: Any, **_kwargs: Any) -> DummyDocument:
                return DummyDocument(b"")

        self.assertTrue(
            isinstance(
                request("http://example.com", client=DummyHttpClient), DummyDocument
            )
        )
