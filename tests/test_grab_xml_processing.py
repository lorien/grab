from test_server import Response

from grab import request
from grab.document import Document
from tests.util import BaseTestCase


class GrabXMLProcessingTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    def test_xml_with_declaration(self) -> None:
        self.server.add_response(
            Response(
                data=b'<?xml version="1.0" encoding="UTF-8"?>'
                b"<root><foo>foo</foo></root>"
            )
        )
        doc = request(self.server.get_url())
        self.assertTrue(doc.select("//foo").text() == "foo")

    def test_declaration_bug(self) -> None:
        # 1. Build Grab instance with XML with xml declaration
        # 2. Call search method
        # 3. Call xpath
        # 4. Get ValueError: Unicode strings with encoding
        #     declaration are not supported.
        xml = b'<?xml version="1.0" encoding="UTF-8"?><tree><leaf>text</leaf></tree>'
        doc = Document(xml)
        self.assertTrue(doc.text_search("text"))
        self.assertEqual(doc.select("//leaf").text(), "text")

        # Similar bugs
        doc = Document(xml)
        self.assertTrue(doc.rex_search("text"))
        self.assertEqual(doc.select("//leaf").text(), "text")
