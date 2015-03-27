# coding: utf-8
from test.util import build_grab
from test.util import BaseGrabTestCase


class TestContentLimit(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_nobody(self):
        g = build_grab()
        g.setup(nobody=True)
        self.server.response['get.data'] = 'foo'
        g.go(self.server.get_url())
        self.assertEqual(b'', g.response.body)
        self.assertTrue(len(g.response.head) > 0)

    def test_body_maxsize(self):
        g = build_grab()
        g.setup(body_maxsize=100)
        self.server.response['get.data'] = 'x' * 1024 * 1024
        g.go(self.server.get_url())
        # Should be less 50kb
        self.assertTrue(len(g.response.body) < 50000)
