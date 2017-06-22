# coding: utf-8
from tests.util import build_grab
from tests.util import BaseGrabTestCase
from grab.error import GrabTimeoutError


class GrabTimeoutCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_timeout(self):

        def callback(server):
            server.set_status(200)
            server.write('x')
            server.write('y')
            for _ in range(4):
                yield {'type': 'sleep', 'time': 0.5}
                server.write('y')
                server.flush()
            server.finish()

        self.server.response['callback'] = callback
        grab = build_grab()
        grab.setup(timeout=1, url=self.server.get_url())
        self.assertRaises(GrabTimeoutError, grab.request)
