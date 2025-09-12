# coding: utf-8
import time

from grab.error import GrabTimeoutError
from test_server import Response
from tests.util import BaseGrabTestCase, build_grab


class GrabTimeoutCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_timeout(self):
        def callback():
            time.sleep(0.2)
            return {
                "type": "response",
                "data": b"zzz",
            }

        self.server.add_response(Response(callback=callback))
        grab = build_grab()
        grab.setup(timeout=0.1, url=self.server.get_url())
        self.assertRaises(GrabTimeoutError, grab.request)
