from test_server import Response

from tests.util import BaseGrabTestCase, build_grab


class LXMLExtensionTest(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_dash_issue(self):
        html = b"<strong>&#151;</strong>"
        self.server.add_response(Response(data=html), count=3)
        grab = build_grab()
        grab.go(self.server.get_url())

        # By default &#[128-160]; are fixed
        self.assertFalse(grab.doc.select("//strong/text()").text() == chr(151))
        self.assertTrue(grab.doc.select("//strong/text()").text() == chr(8212))

        # disable fix-behaviour
        grab.setup(fix_special_entities=False)
        grab.go(self.server.get_url())

        # By default &#[128-160]; are fixed
        self.assertTrue(grab.doc.select("//strong/text()").text() == chr(151))
        self.assertFalse(grab.doc.select("//strong/text()").text() == chr(8212))

        # Explicitly use unicode_body func
        grab = build_grab()
        grab.go(self.server.get_url())
        # print(':::', grab.doc.unicode_body())
        self.assertTrue("&#8212;" in grab.doc.unicode_body())

    def test_invalid_charset(self):
        html = b"""<head><meta http-equiv="Content-Type"
                    content="text/html; charset=windows-874">'
                    </head><body>test</body>"""
        self.server.add_response(Response(data=html))
        grab = build_grab()
        grab.go(self.server.get_url())
        # print(grab.doc.charset)
