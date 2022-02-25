from pprint import pprint  # pylint: disable=unused-import
from email.message import EmailMessage

from test_server import Response  # pylint: disable=unused-import

from tests.util import build_grab  # pylint: disable=unused-import
from tests.util import BaseGrabTestCase


class TestMisc(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    # *****************
    # grab.request_head
    # *****************

    def test_request_headers_default(self):
        grab = build_grab()
        self.assertTrue(grab.request_headers is None)

    def test_request_headers_debug_false(self):
        self.server.add_response(Response())
        grab = build_grab(debug=False)
        grab.go(self.server.get_url(), headers=[("User-Agent", "GRAB")])
        self.assertTrue(isinstance(grab.request_headers, EmailMessage))
        self.assertTrue(len(grab.request_headers) == 0)

    def test_request_headers_debug_true(self):
        self.server.add_response(Response())
        grab = build_grab(debug=True)
        grab.go(self.server.get_url(), headers=[("User-Agent", "GRAB")])
        self.assertEqual(grab.request_headers["user-agent"], "GRAB")

    # *****************
    # grab.request_head
    # *****************

    def test_request_head_default(self):
        grab = build_grab()
        self.assertTrue(grab.request_headers is None)

    def test_request_head_debug_false(self):
        self.server.add_response(Response())
        grab = build_grab(debug=False)
        grab.go(self.server.get_url())
        self.assertEqual(grab.request_head, b"")

    def test_request_head_debug_true(self):
        self.server.add_response(Response())
        grab = build_grab(debug=True)
        grab.go(self.server.get_url())
        self.assertTrue(grab.request_head.startswith(b"GET /"))
