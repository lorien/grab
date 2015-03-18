# coding: utf-8
"""
This test fails in py3.3 environment because `grab.response.body`
contains <str>, but it should contains <bytes>
"""
from test.util import build_grab
from test.util import BaseGrabTestCase


class GrabCharsetDetectionTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_document_charset_option(self):
        g = build_grab()
        self.server.response['get.data'] = b'foo'
        g.go(self.server.get_url())
        self.assertEqual(b'foo', g.response.body)

        g = build_grab()
        self.server.response['get.data'] = u'фуу'.encode('utf-8')
        g.go(self.server.get_url())
        self.assertEqual(u'фуу'.encode('utf-8'), g.response.body)

        print(g.response.head)
        self.assertEqual(g.response.charset, 'utf-8')

        g = build_grab(document_charset='cp1251')
        self.server.response['get.data'] = u'фуу'.encode('cp1251')
        g.go(self.server.get_url())
        self.assertEqual(u'фуу'.encode('cp1251'), g.response.body)
        self.assertEqual(g.response.charset, 'cp1251')

    def test_document_charset_lowercase(self):
        self.server.response['charset'] = 'UTF-8'
        g = build_grab()
        g.go(self.server.get_url())
        self.assertEquals('utf-8', g.doc.charset)
