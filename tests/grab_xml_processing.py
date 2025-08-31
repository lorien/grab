# coding: utf-8
from tests.util import build_grab
from tests.util import BaseGrabTestCase


class GrabXMLProcessingTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_xml_with_declaration(self):
        self.server.response['get.data'] =\
            b'<?xml version="1.0" encoding="UTF-8"?>'\
            b'<root><foo>foo</foo></root>'
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertTrue(grab.doc.select('//foo').text() == 'foo')

    def test_declaration_bug(self):
        """
        1. Build Grab instance with XML with xml declaration
        2. Call search method
        3. Call xpath
        4. Get ValueError: Unicode strings with encoding
            declaration are not supported.
        """
        xml = b'<?xml version="1.0" encoding="UTF-8"?>'\
              b'<tree><leaf>text</leaf></tree>'
        grab = build_grab(document_body=xml)
        self.assertTrue(grab.doc.text_search(u'text'))
        self.assertEqual(grab.doc.select('//leaf').text(), u'text')

        # Similar bugs
        grab = build_grab(document_body=xml)
        self.assertTrue(grab.doc.rex_search(u'text'))
        self.assertEqual(grab.doc.select('//leaf').text(), u'text')
