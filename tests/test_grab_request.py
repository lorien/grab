from __future__ import annotations

from typing import Any

from test_server import Response

from grab import request
from tests.util import BaseTestCase


class GrabRequestTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    def test_get_method(self) -> None:
        self.server.add_response(Response())
        request(self.server.get_url())
        self.assertEqual("GET", self.server.request.method)

    def test_delete_method(self) -> None:
        self.server.add_response(Response())
        request(self.server.get_url(), method="DELETE")
        self.assertEqual("DELETE", self.server.request.method)

    def test_put_method(self) -> None:
        self.server.add_response(Response())
        request(self.server.get_url(), method="PUT", body=b"abc")
        self.assertEqual("PUT", self.server.request.method)
        self.assertEqual("3", self.server.request.headers.get("content-length"))

    def test_head_with_invalid_bytes(self) -> None:
        def callback() -> dict[str, Any]:
            return {
                "type": "response",
                "status": 200,
                "headers": [("Hello-Bug", b"start\xa0end")],
                "data": b"",
            }

        self.server.add_response(Response(callback=callback))
        request(self.server.get_url())

    # def test_options_method(self):
    #    self.server.add_response(Response())
    #    grab.setup(method="OPTIONS")
    #    request(self.server.get_url())
    #    self.assertEqual("OPTIONS", self.server.request.method)
    #    self.assertEqual("3", self.server.request.headers.get("content-length"))

    #    self.server.add_response(Response())
    #    grab.setup(method="OPTIONS")
    #    request(self.server.get_url())
    #    self.assertEqual("OPTIONS", self.server.request.method)
    #    self.assertTrue("Content-Length" not in self.server.request.headers)
