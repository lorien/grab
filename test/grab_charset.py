# coding: utf-8
"""
This test fails in py3.3 environment because `grab.response.body`
contains <str>, but it should contains <bytes>
"""
from grab import Grab
from test.util import build_grab
from test.util import BaseGrabTestCase

from grab.util.py3k_support import *  # noqa


class GrabCharsetDetectionTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_document_charset_option(self):
        g = build_grab()
        self.server.response['get.data'] = 'foo'
        g.go(self.server.get_url())
        self.assertEqual('foo', g.response.body)

        g = build_grab()
        self.server.response['get.data'] = u'фуу'.encode('utf-8')
        g.go(self.server.get_url())
        self.assertEqual(u'фуу'.encode('utf-8'), g.response.body)
        self.assertEqual(g.response.charset, 'utf-8')

        g = Grab(transport=GRAB_TRANSPORT, document_charset='cp1251')
        self.server.response['get.data'] = u'фуу'.encode('cp1251')
        g.go(self.server.get_url())
        self.assertEqual(u'фуу'.encode('cp1251'), g.response.body)
        self.assertEqual(g.response.charset, 'cp1251')
