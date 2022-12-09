from email.message import EmailMessage
from pprint import pprint  # pylint: disable=unused-import

from test_server import Response  # pylint: disable=unused-import

from tests.util import build_grab  # pylint: disable=unused-import
from tests.util import BaseGrabTestCase


class TestMisc(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_request_headers_default(self):
        grab = build_grab()
        self.assertTrue(grab.request_headers is None)
        self.assertTrue(grab.request_head is None)

    def test_request_headers_live(self):
        self.server.add_response(Response())
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertTrue(isinstance(grab.request_headers, EmailMessage))
        self.assertTrue(len(grab.request_headers) == 0)
        self.assertTrue(grab.request_head == b"")
