import time

from test_server import Response

from grab.error import GrabTimeoutError
from tests.util import BaseGrabTestCase, build_grab


class GrabTimeoutCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_timeout(self):
        def callback():
            time.sleep(2)
            return {
                "type": "response",
                "data": b"zzz",
            }

        self.server.add_response(Response(callback=callback))
        grab = build_grab()
        grab.setup(timeout=1, url=self.server.get_url())
        self.assertRaises(GrabTimeoutError, grab.request)
