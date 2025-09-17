# coding: utf-8
import six
from test_server import Request, Response

from tests.util import BaseGrabTestCase, build_grab


class LXMLExtensionTest(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_parsing_control_code_entity(self):
        html = "<strong>&#128;</strong>"
        self.server.add_response(Response(data=html))
        grab = build_grab()
        grab.go(self.server.get_url())

        node = grab.doc.select("//strong/text()")
        # fmt: off
        self.assertEqual(node.text(), u"€")
        # fmt: on

    def test_invalid_charset(self):
        html = """<head><meta http-equiv="Content-Type"
                   content="text/html; charset=windows-874">'
                   </head><body>test</body>"""
        self.server.add_response(Response(data=html))
        grab = build_grab()
        grab.go(self.server.get_url())
        # print(grab.doc.charset)
