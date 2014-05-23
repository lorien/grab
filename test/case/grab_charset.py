# coding: utf-8
"""
This test fails in py3.3 environment because `grab.response.body`
contains <str>, but it should contains <bytes>
"""
from unittest import TestCase
import json

from grab import Grab, GrabMisuseError
from test.util import ignore_transport, only_transport, build_grab
from test.server import SERVER
from grab.extension import register_extensions

from grab.util.py3k_support import *

class GrabCharsetDetectionTestCase(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_document_charset_option(self):
        g = build_grab()
        SERVER.RESPONSE['get'] = 'foo'
        g.go(SERVER.BASE_URL)
        self.assertEqual('foo', g.response.body)

        g = build_grab()
        SERVER.RESPONSE['get'] = u'фуу'.encode('utf-8')
        g.go(SERVER.BASE_URL)
        self.assertEqual(u'фуу'.encode('utf-8'), g.response.body)
        self.assertEqual(g.response.charset, 'utf-8')

        g = Grab(transport=GRAB_TRANSPORT, document_charset='cp1251')
        SERVER.RESPONSE['get'] = u'фуу'.encode('cp1251')
        g.go(SERVER.BASE_URL)
        self.assertEqual(u'фуу'.encode('cp1251'), g.response.body)
        self.assertEqual(g.response.charset, 'cp1251')
