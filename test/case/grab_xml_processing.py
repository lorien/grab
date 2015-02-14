# coding: utf-8
from unittest import TestCase

from grab import Grab
from test.util import ignore_transport, only_transport, build_grab
from test.server import SERVER

class GrabXMLProcessingTestCase(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_xml_with_declaration(self):
        SERVER.RESPONSE['get'] = b'<?xml version="1.0" encoding="UTF-8"?><root><foo>foo</foo></root>'
        g = build_grab()
        g.go(SERVER.BASE_URL)
        self.assertTrue(g.xpath_one('//foo').text == 'foo')

    def test_declaration_bug(self):
        """
        1. Build Grab instance with XML with xml declaration
        2. Call search method
        3. Call xpath
        4. Get ValueError: Unicode strings with encoding declaration are not supported.
        """
        xml = b'<?xml version="1.0" encoding="UTF-8"?><tree><leaf>text</leaf></tree>'
        g = build_grab(document_body=xml)
        self.assertTrue(g.search(u'text'))
        self.assertEqual(g.xpath_one('//leaf').text, u'text')

        # Similar bugs
        g = build_grab(document_body=xml)
        self.assertTrue(g.rex(u'text'))
        self.assertEqual(g.xpath_one('//leaf').text, u'text')
