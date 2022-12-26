from test_server import Response

from grab import request
from tests.util import BaseTestCase


class GrabSimpleTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    def test_get(self) -> None:
        self.server.add_response(Response(data=b"Final Countdown"))
        doc = request(self.server.get_url())
        self.assertTrue(b"Final Countdown" in doc.body)

    def test_body_content(self) -> None:
        self.server.add_response(Response(data=b"Simple String"))
        doc = request(self.server.get_url())
        self.assertEqual(b"Simple String", doc.body)

    def test_status_code(self) -> None:
        self.server.add_response(Response(data=b"Simple String"))
        doc = request(self.server.get_url())
        self.assertEqual(200, doc.code)

    def test_parsing_response_headers(self) -> None:
        self.server.add_response(Response(headers=[("Hello", "Grab")]))
        doc = request(self.server.get_url())
        self.assertTrue(doc.headers["Hello"] == "Grab")
