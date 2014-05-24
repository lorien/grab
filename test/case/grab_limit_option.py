# coding: utf-8
from unittest import TestCase

from grab import Grab
from test.util import ignore_transport, build_grab
from test.server import SERVER

class TestContentLimit(TestCase):
    def setUp(self):
        SERVER.reset()

    @ignore_transport('grab.transport.requests.RequestsTransport')
    def test_nobody(self):
        g = build_grab()
        g.setup(nobody=True)
        SERVER.RESPONSE['get'] = 'foo'
        g.go(SERVER.BASE_URL)
        self.assertEqual(b'', g.response.body)
        self.assertTrue(len(g.response.head) > 0)

    @ignore_transport('grab.transport.requests.RequestsTransport')
    def test_body_maxsize(self):
        g = build_grab()
        g.setup(body_maxsize=100)
        SERVER.RESPONSE['get'] = 'x' * 1024 * 1024
        g.go(SERVER.BASE_URL)
        # Should be less 50kb
        self.assertTrue(len(g.response.body) < 50000)
