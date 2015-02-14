# coding: utf-8
from unittest import TestCase
import os

from grab import Grab, GrabMisuseError
from test.util import TMP_DIR, ignore_transport, only_transport, build_grab
from test.server import SERVER
from grab.extension import register_extensions


class GrabSimpleTestCase(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_get(self):
        SERVER.RESPONSE['get'] = 'Final Countdown'
        g = build_grab()
        g.go(SERVER.BASE_URL)
        self.assertTrue(b'Final Countdown' in g.response.body)

    def test_body_content(self):
        SERVER.RESPONSE['get'] = 'Simple String'
        g = build_grab()
        g.go(SERVER.BASE_URL)
        self.assertEqual(b'Simple String', g.response.body)
        #self.assertEqual('Simple String' in g.response.runtime_body)

    def test_status_code(self):
        SERVER.RESPONSE['get'] = 'Simple String'
        g = build_grab()
        g.go(SERVER.BASE_URL)
        self.assertEqual(200, g.response.code)

    def test_parsing_response_headers(self):
        SERVER.RESPONSE['headers'] = [('Hello', 'Grab')]
        g = build_grab()
        g.go(SERVER.BASE_URL)
        self.assertTrue(g.response.headers['Hello'] == 'Grab')

    def test_depreated_hammer_mode_options(self):
        SERVER.RESPONSE['get'] = 'foo'
        g = build_grab()
        g.setup(hammer_mode=True)
        g.go(SERVER.BASE_URL)

        g.setup(hammer_timeouts=((1, 1), (2, 2)))
        g.go(SERVER.BASE_URL)
