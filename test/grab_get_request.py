# coding: utf-8
from test.util import build_grab
from test.util import BaseGrabTestCase


class GrabSimpleTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_get(self):
        self.server.response['get.data'] = 'Final Countdown'
        g = build_grab()
        g.go(self.server.get_url())
        self.assertTrue(b'Final Countdown' in g.response.body)

    def test_body_content(self):
        self.server.response['get.data'] = 'Simple String'
        g = build_grab()
        g.go(self.server.get_url())
        self.assertEqual(b'Simple String', g.response.body)
        # self.assertEqual('Simple String' in g.response.runtime_body)

    def test_status_code(self):
        self.server.response['get.data'] = 'Simple String'
        g = build_grab()
        g.go(self.server.get_url())
        self.assertEqual(200, g.response.code)

    def test_parsing_response_headers(self):
        self.server.response['headers'] = [('Hello', 'Grab')]
        g = build_grab()
        g.go(self.server.get_url())
        self.assertTrue(g.response.headers['Hello'] == 'Grab')

    def test_depreated_hammer_mode_options(self):
        self.server.response['get.data'] = 'foo'
        g = build_grab()
        g.setup(hammer_mode=True)
        g.go(self.server.get_url())

        g.setup(hammer_timeouts=((1, 1), (2, 2)))
        g.go(self.server.get_url())
