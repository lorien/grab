from test_server import Response

from tests.util import BaseGrabTestCase, build_grab


class GrabSimpleTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_get(self):
        self.server.add_response(Response(data=b"Final Countdown"))
        grab = build_grab()
        doc = grab.request(self.server.get_url())
        self.assertTrue(b"Final Countdown" in doc.body)

    def test_body_content(self):
        self.server.add_response(Response(data=b"Simple String"))
        grab = build_grab()
        doc = grab.request(self.server.get_url())
        self.assertEqual(b"Simple String", doc.body)

    def test_status_code(self):
        self.server.add_response(Response(data=b"Simple String"))
        grab = build_grab()
        doc = grab.request(self.server.get_url())
        self.assertEqual(200, doc.code)

    def test_parsing_response_headers(self):
        self.server.add_response(Response(headers=[("Hello", "Grab")]))
        grab = build_grab()
        doc = grab.request(self.server.get_url())
        self.assertTrue(doc.headers["Hello"] == "Grab")
