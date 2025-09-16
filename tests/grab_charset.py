# coding: utf-8
"""
This test fails in py3.3 environment because `grab.doc.body`
contains <str>, but it should contains <bytes>
"""
import six
from test_server import Request, Response

from grab import Grab
from tests.util import BaseGrabTestCase, build_grab


class GrabCharsetDetectionTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_document_charset_option(self):
        grab = build_grab()
        self.server.add_response(Response(data="foo"))
        grab.go(self.server.get_url())
        self.assertEqual(b"foo", grab.doc.body)

        grab = build_grab()
        # fmt: off
        self.server.add_response(Response(data=u"фуу".encode("utf-8")))
        grab.go(self.server.get_url())
        self.assertEqual(u"фуу".encode("utf-8"), grab.doc.body)
        # fmt: on

        # print(grab.doc.head)
        self.assertEqual(grab.doc.charset, "utf-8")

        grab = build_grab(document_charset="cp1251")
        # fmt: off
        self.server.add_response(Response(data=u"фуу".encode("cp1251")))
        grab.go(self.server.get_url())
        self.assertEqual(u"фуу".encode("cp1251"), grab.doc.body)
        # fmt: on
        # cp1251 will be normalized to windows-1251
        self.assertEqual(grab.doc.charset, "windows-1251")

    # def test_document_charset_lowercase(self):
    #    self.server.response["charset"] = "UTF-8"
    #    grab = build_grab()
    #    grab.go(self.server.get_url())
    #    self.assertEqual("utf-8", grab.doc.charset)

    def test_dash_issue(self):
        html = "<strong>&#151;</strong>"
        self.server.add_response(Response(data=html))
        grab = build_grab()
        grab.go(self.server.get_url())

        # By default &#[128-160]; are fixed
        self.assertNotEqual(grab.doc.select("//strong/text()").text(), six.unichr(151))
        self.assertEqual(grab.doc.select("//strong/text()").text(), six.unichr(8212))

        # TODO: does not work in py3
        # for some reason document._grab_config
        # contains cached value of fix_special_entites setting
        # # disable fix-behaviour
        # grab.setup(fix_special_entities=False)
        # self.server.add_response(Response(data=html))
        # grab.go(self.server.get_url())

        # # Now, &#[128-160]; must be parsed in a wrong way
        # # self.assertEqual(grab.doc.select("//strong/text()").text(), six.unichr(151))
        # self.assertNotEqual(grab.doc.select("//strong/text()").text(), six.unichr(8212))

        # Explicitly use unicode_body func
        grab = build_grab()
        self.server.add_response(Response(data=html))
        grab.go(self.server.get_url())
        # print(':::', grab.doc.unicode_body())
        self.assertTrue("&#8212;" in grab.doc.unicode_body())

    def test_invalid_charset(self):
        html = """<head><meta http-equiv="Content-Type"
                    content="text/html; charset=windows-874">'
                    </head><body>test</body>"""
        self.server.add_response(Response(data=html), count=1, method="get")
        grab = build_grab()
        grab.go(self.server.get_url())
        # print(grab.doc.charset)

    def test_charset_html5(self):
        grab = Grab()
        grab.setup_document(b"<meta charset='windows-1251'>")
        self.assertEqual("windows-1251", grab.doc.charset)

        grab.setup_document(b'<meta charset="windows-1252">')
        self.assertEqual("windows-1252", grab.doc.charset)

        grab.setup_document(b"<meta charset=latin-1>")
        self.assertEqual("latin-1", grab.doc.charset)

        grab.setup_document(b"<meta charset  =  'windows-1251'  >")
        self.assertEqual("windows-1251", grab.doc.charset)

        grab.setup_document(b'<meta charset  =  "windows-1252"   >')
        self.assertEqual("windows-1252", grab.doc.charset)

        grab.setup_document(b"<meta charset  =  latin-1  >")
        self.assertEqual("latin-1", grab.doc.charset)
