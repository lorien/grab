# coding: utf-8
"""
This test fails in py3.3 environment because `grab.doc.body`
contains <str>, but it should contains <bytes>
"""
import six

from tests.util import build_grab
from tests.util import BaseGrabTestCase
from grab import Grab


class GrabCharsetDetectionTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_document_charset_option(self):
        grab = build_grab()
        self.server.response['get.data'] = b'foo'
        grab.go(self.server.get_url())
        self.assertEqual(b'foo', grab.doc.body)

        grab = build_grab()
        self.server.response['get.data'] = u'фуу'.encode('utf-8')
        grab.go(self.server.get_url())
        self.assertEqual(u'фуу'.encode('utf-8'), grab.doc.body)

        #print(grab.doc.head)
        self.assertEqual(grab.doc.charset, 'utf-8')

        grab = build_grab(document_charset='cp1251')
        self.server.response['get.data'] = u'фуу'.encode('cp1251')
        grab.go(self.server.get_url())
        self.assertEqual(u'фуу'.encode('cp1251'), grab.doc.body)
        self.assertEqual(grab.doc.charset, 'cp1251')

    def test_document_charset_lowercase(self):
        self.server.response['charset'] = 'UTF-8'
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertEqual('utf-8', grab.doc.charset)

    def test_dash_issue(self):
        html = '<strong>&#151;</strong>'
        self.server.response['get.data'] = html
        grab = build_grab()
        grab.go(self.server.get_url())

        # By default &#[128-160]; are fixed
        self.assertFalse(grab.doc.select('//strong/text()').text()
                         == six.unichr(151))
        self.assertTrue(grab.doc.select('//strong/text()').text()
                        == six.unichr(8212))

        # disable fix-behaviour
        grab.setup(fix_special_entities=False)
        grab.go(self.server.get_url())

        # By default &#[128-160]; are fixed
        self.assertTrue(grab.doc.select('//strong/text()').text()
                        == six.unichr(151))
        self.assertFalse(grab.doc.select('//strong/text()').text()
                         == six.unichr(8212))

        # Explicitly use unicode_body func
        grab = build_grab()
        grab.go(self.server.get_url())
        #print(':::', grab.doc.unicode_body())
        self.assertTrue('&#8212;' in grab.doc.unicode_body())

    def test_invalid_charset(self):
        html = '''<head><meta http-equiv="Content-Type"
                    content="text/html; charset=windows-874">'
                    </head><body>test</body>'''
        self.server.response['get.data'] = html
        grab = build_grab()
        grab.go(self.server.get_url())
        #print(grab.doc.charset)

    def test_charset_html5(self):
        grab = Grab()
        grab.setup_document(b"<meta charset='windows-1251'>")
        self.assertEqual('windows-1251', grab.doc.charset)

        grab.setup_document(b'<meta charset="windows-1252">')
        self.assertEqual('windows-1252', grab.doc.charset)

        grab.setup_document(b'<meta charset=latin-1>')
        self.assertEqual('latin-1', grab.doc.charset)

        grab.setup_document(b"<meta charset  =  'windows-1251'  >")
        self.assertEqual('windows-1251', grab.doc.charset)

        grab.setup_document(b'<meta charset  =  "windows-1252"   >')
        self.assertEqual('windows-1252', grab.doc.charset)

        grab.setup_document(b'<meta charset  =  latin-1  >')
        self.assertEqual('latin-1', grab.doc.charset)
