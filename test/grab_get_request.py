# coding: utf-8
from unittest import TestCase
import os

from grab import Grab, GrabMisuseError
from .util import (GRAB_TRANSPORT, TMP_DIR,
                   ignore_transport, only_transport)
from .tornado_util import SERVER
from grab.extension import register_extensions


class GrabSimpleTestCase(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_get(self):
        SERVER.RESPONSE['get'] = 'Final Countdown'
        g = Grab(transport=GRAB_TRANSPORT)
        g.go(SERVER.BASE_URL)
        self.assertTrue('Final Countdown' in g.response.body)

    def test_body_content(self):
        SERVER.RESPONSE['get'] = 'Simple String'
        g = Grab(transport=GRAB_TRANSPORT)
        g.go(SERVER.BASE_URL)
        self.assertEqual('Simple String', g.response.body)
        #self.assertEqual('Simple String' in g.response.runtime_body)

    def test_status_code(self):
        SERVER.RESPONSE['get'] = 'Simple String'
        g = Grab(transport=GRAB_TRANSPORT)
        g.go(SERVER.BASE_URL)
        self.assertEqual(200, g.response.code)

    def test_parsing_response_headers(self):
        SERVER.RESPONSE['headers'] = [('Hello', 'Grab')]
        g = Grab(transport=GRAB_TRANSPORT)
        g.go(SERVER.BASE_URL)
        self.assertTrue(g.response.headers['Hello'] == 'Grab')
