# coding: utf-8
from tests.util import build_grab
from tests.util import BaseGrabTestCase


class GrabSimpleTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_get(self):
        self.server.response['get.data'] = 'Final Countdown'
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertTrue(b'Final Countdown' in grab.doc.body)

    def test_body_content(self):
        self.server.response['get.data'] = 'Simple String'
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertEqual(b'Simple String', grab.doc.body)
        # self.assertEqual('Simple String' in grab.doc.runtime_body)

    def test_status_code(self):
        self.server.response['get.data'] = 'Simple String'
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertEqual(200, grab.doc.code)

    def test_parsing_response_headers(self):
        self.server.response['headers'] = [('Hello', 'Grab')]
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertTrue(grab.doc.headers['Hello'] == 'Grab')
