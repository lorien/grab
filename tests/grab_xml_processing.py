from test_server import Response
from tests.util import BaseGrabTestCase, build_grab


class GrabXMLProcessingTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_xml_with_declaration(self):
        self.server.add_response(
            Response(
                data=b'<?xml version="1.0" encoding="UTF-8"?>'
                b"<root><foo>foo</foo></root>"
            )
        )
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertTrue(grab.doc.select("//foo").text() == "foo")

    def test_declaration_bug(self):
        # 1. Build Grab instance with XML with xml declaration
        # 2. Call search method
        # 3. Call xpath
        # 4. Get ValueError: Unicode strings with encoding
        #     declaration are not supported.
        xml = (
            b'<?xml version="1.0" encoding="UTF-8"?>' b"<tree><leaf>text</leaf></tree>"
        )
        grab = build_grab(document_body=xml)
        self.assertTrue(grab.doc.text_search("text"))
        self.assertEqual(grab.doc.select("//leaf").text(), "text")

        # Similar bugs
        grab = build_grab(document_body=xml)
        self.assertTrue(grab.doc.rex_search("text"))
        self.assertEqual(grab.doc.select("//leaf").text(), "text")
