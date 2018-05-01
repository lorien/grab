# coding: utf-8
import time

from tests.util import build_grab
from tests.util import BaseGrabTestCase
from grab.error import GrabTimeoutError


class GrabTimeoutCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_timeout(self):

        def callback():
            time.sleep(2)
            return {
                'type': 'response',
                'body': b'zzz',
            }

        self.server.response['callback'] = callback
        grab = build_grab()
        grab.setup(timeout=1, url=self.server.get_url())
        self.assertRaises(GrabTimeoutError, grab.request)
