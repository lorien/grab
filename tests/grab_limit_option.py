# coding: utf-8
from tests.util import build_grab
from tests.util import BaseGrabTestCase


class TestContentLimit(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_nobody(self):
        grab = build_grab()
        grab.setup(nobody=True)
        self.server.response['get.data'] = 'foo'
        grab.go(self.server.get_url())
        self.assertEqual(b'', grab.doc.body)
        self.assertTrue(len(grab.doc.head) > 0)

    def test_body_maxsize(self):
        grab = build_grab()
        grab.setup(body_maxsize=100)
        self.server.response['get.data'] = 'x' * 1024 * 1024
        grab.go(self.server.get_url())
        # Should be less 50kb
        self.assertTrue(len(grab.doc.body) < 50000)
