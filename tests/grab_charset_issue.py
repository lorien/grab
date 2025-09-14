# coding: utf-8
import six

from test_server import Request, Response
from tests.util import BaseGrabTestCase, build_grab


class LXMLExtensionTest(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_dash_issue(self):
        html = "<strong>&#151;</strong>"
        self.server.add_response(Response(data=html))
        grab = build_grab()
        grab.go(self.server.get_url())

        # By default &#[128-160]; are fixed
        node = grab.doc.select("//strong/text()")
        print(type(node))
        self.assertFalse(node.text() == six.unichr(151))
        self.assertTrue(grab.doc.select("//strong/text()").text() == six.unichr(8212))

    #    self.server.add_response(Response(data=html))
    #    # disable fix-behaviour
    #    grab.setup(fix_special_entities=False)
    #    grab.go(self.server.get_url())

    #    # By default &#[128-160]; are fixed
    #    self.assertTrue(grab.doc.select("//strong/text()").text() == six.unichr(151))
    #    self.assertFalse(grab.doc.select("//strong/text()").text() == six.unichr(8212))

    #    self.server.add_response(Response(data=html))
    #    # Explicitly use unicode_body func
    #    grab = build_grab()
    #    grab.go(self.server.get_url())
    #    # print(':::', grab.doc.unicode_body())
    #    self.assertTrue("&#8212;" in grab.doc.unicode_body())

    # def test_invalid_charset(self):
    #    html = """<head><meta http-equiv="Content-Type"
    #                content="text/html; charset=windows-874">'
    #                </head><body>test</body>"""
    #    self.server.add_response(Response(data=html))
    #    grab = build_grab()
    #    grab.go(self.server.get_url())
    #    # print(grab.doc.charset)
