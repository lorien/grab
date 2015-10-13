# coding: utf-8
"""
This test fails in py3.3 environment because `grab.response.body`
contains <str>, but it should contains <bytes>
"""
import six

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


    def test_dash_issue(self):
        HTML = '<strong>&#151;</strong>'
        self.server.response['get.data'] = HTML
        g = build_grab()
        g.go(self.server.get_url())

        # By default &#[128-160]; are fixed
        self.assertFalse(g.xpath_one('//strong/text()') == six.unichr(151))
        self.assertTrue(g.xpath_one('//strong/text()') == six.unichr(8212))

        # disable fix-behaviour
        g.setup(fix_special_entities=False)
        g.go(self.server.get_url())

        # By default &#[128-160]; are fixed
        self.assertTrue(g.xpath_one('//strong/text()') == six.unichr(151))
        self.assertFalse(g.xpath_one('//strong/text()') == six.unichr(8212))

        # Explicitly use unicode_body func
        g = build_grab()
        g.go(self.server.get_url())
        print(':::', g.response.unicode_body())
        self.assertTrue('&#8212;' in g.response.unicode_body())

    def test_invalid_charset(self):
        HTML = '''<head><meta http-equiv="Content-Type"
                    content="text/html; charset=windows-874">'
                    </head><body>test</body>'''
        self.server.response['get.data'] = HTML
        g = build_grab()
        g.go(self.server.get_url())
        #print(g.doc.charset)
