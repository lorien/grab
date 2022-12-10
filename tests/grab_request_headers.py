from pprint import pprint  # pylint: disable=unused-import

from test_server import Response  # pylint: disable=unused-import

from tests.util import build_grab  # pylint: disable=unused-import
from tests.util import BaseGrabTestCase


class TestMisc(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_request_headers_default(self):
        grab = build_grab()
        with self.assertRaises(AttributeError):
            # pylint: disable=no-member
            print(grab.request_headers)
            print(grab.request_head)

    def test_request_headers_live(self):
        self.server.add_response(Response())
        grab = build_grab()
        grab.go(self.server.get_url())
        with self.assertRaises(AttributeError):
            # pylint: disable=no-member
            print(grab.request_headers)
            print(grab.request_headers)
            print(grab.request_head)
