from test_server import Response

from grab.error import GrabTimeoutError
from tests.util import BaseGrabTestCase, build_grab


class GrabTimeoutCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_timeout_raises(self):
        self.server.add_response(Response(data=b"zzz", sleep=1))
        grab = build_grab()
        grab.setup(timeout=0.1, url=self.server.get_url())
        self.assertRaises(GrabTimeoutError, grab.request)

    def test_timeout_enough_to_complete(self):
        self.server.add_response(Response(data=b"zzz", sleep=0.5))
        grab = build_grab()
        grab.setup(timeout=2, url=self.server.get_url())
        grab.request()
