from test_server import Response

from grab import request
from tests.util import BaseTestCase


class LXMLExtensionTest(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    def test_dash_issue(self) -> None:
        html = b"<strong>&#151;</strong>"
        self.server.add_response(Response(data=html), count=3)
        doc = request(self.server.get_url())

        # By default &#[128-159]; are fixed
        self.assertFalse(doc.select("//strong/text()").text() == chr(151))
        self.assertTrue(doc.select("//strong/text()").text() == chr(8212))

    def test_invalid_charset(self) -> None:
        html = b"""<head><meta http-equiv="Content-Type"
                    content="text/html; charset=windows-874">'
                    </head><body>test</body>"""
        self.server.add_response(Response(data=html))
        request(self.server.get_url())
