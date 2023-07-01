from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from test_server import Response

from grab import request
from grab.errors import GrabInvalidResponseError, GrabTooManyRedirectsError
from tests.util import BaseTestCase


def build_location_callback(url: str, counter: int) -> Callable[[], dict[str, Any]]:
    meta = {
        "counter": counter,
        "url": url,
    }

    def callback() -> dict[str, Any]:
        if meta["counter"]:
            status = 301
            headers = [("Location", meta["url"])]
            data = b""
        else:
            status = 200
            headers = []
            data = b"done"
        meta["counter"] = cast(int, meta["counter"]) - 1
        return {
            "type": "response",
            "status": status,
            "data": data,
            "headers": headers,
        }

    return callback


class GrabRedirectTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    def test_redirect_limit(self) -> None:
        self.server.add_response(
            Response(callback=build_location_callback(self.server.get_url(), 10)),
            count=-1,
        )

        self.assertRaises(
            GrabTooManyRedirectsError,
            lambda: request(redirect_limit=5, url=self.server.get_url()),
        )

        self.server.add_response(
            Response(callback=build_location_callback(self.server.get_url(), 10)),
            count=-1,
        )
        doc = request(self.server.get_url(), redirect_limit=20)
        self.assertTrue(b"done" in doc.body)

    def test_redirect_utf_location(self) -> None:
        def callback() -> bytes:
            url = (self.server.get_url() + "фыва").encode("utf-8")
            return (
                b"HTTP/1.1 301 OK\nLocation: %s\nLocation-Length: 9\n\ncontent-1" % url
            )

        self.server.add_response(Response(raw_callback=callback))
        self.server.add_response(Response(data=b"content-2"))
        with self.assertRaises(GrabInvalidResponseError):
            request(process_redirect=True, url=self.server.get_url())
