# coding: utf-8
from unittest import TestCase
import os

from grab import Grab, GrabMisuseError
from .util import (FakeServerThread, BASE_URL, RESPONSE, REQUEST,
                   RESPONSE_ONCE, ignore_transport, GRAB_TRANSPORT,
                   ignore_transport, only_transport)
from .flask_util import FlaskServer
from grab.extension import register_extensions


class TestFlask(TestCase):
    def __init__(self, *args, **kwargs):
        self.server_started = False
        super(TestFlask, self).__init__(*args, **kwargs)

    def setUp(self):
        if not self.server_started:
            self.server_started = True
            self.server = FlaskServer()
            self.server.start()

    def tearDown(self):
        pass

    def test_flask(self):
        g = Grab(transport=GRAB_TRANSPORT)
        g.go(BASE_URL + '?foo=4')
        self.assertEqual(self.server.request_info['GET']['foo'], '4')

    def test_flask2(self):
        g = Grab(transport=GRAB_TRANSPORT)
        g.go(BASE_URL + '?foo=5')
        self.assertEqual(self.server.request_info['GET']['foo'], '5')
