from grab import Grab
from test_server import Response
from tests.util import BaseGrabTestCase, build_grab


class GrabCharsetDetectionTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_document_charset_option(self):
        grab = build_grab()
        self.server.add_response(Response(data=b"foo"))
        grab.go(self.server.get_url())
        self.assertEqual(b"foo", grab.doc.body)

        grab = build_grab()
        self.server.add_response(Response(data="фуу".encode("utf-8")))
        grab.go(self.server.get_url())
        self.assertEqual("фуу".encode("utf-8"), grab.doc.body)

        # print(grab.doc.head)
        self.assertEqual(grab.doc.charset, "utf-8")

        grab = build_grab(document_charset="cp1251")
        self.server.add_response(Response(data="фуу".encode("cp1251")))
        grab.go(self.server.get_url())
        self.assertEqual("фуу".encode("cp1251"), grab.doc.body)
        self.assertEqual(grab.doc.charset, "cp1251")

    def test_document_charset_lowercase(self):
        self.server.add_response(
            Response(headers=[("Content-Type", "tex/html; charset=cp1251")])
        )
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertEqual("cp1251", grab.doc.charset)

    def test_dash_issue(self):
        html = b"<strong>&#151;</strong>"
        self.server.add_response(Response(data=html))
        grab = build_grab()
        grab.go(self.server.get_url())

        # By default &#[128-160]; are fixed
        self.assertFalse(grab.doc.select("//strong/text()").text() == chr(151))
        self.assertTrue(grab.doc.select("//strong/text()").text() == chr(8212))

        # disable fix-behaviour
        self.server.add_response(Response(data=html))
        grab.setup(fix_special_entities=False)
        grab.go(self.server.get_url())

        # By default &#[128-160]; are fixed
        self.assertTrue(grab.doc.select("//strong/text()").text() == chr(151))
        self.assertFalse(grab.doc.select("//strong/text()").text() == chr(8212))

        # Explicitly use unicode_body func
        self.server.add_response(Response(data=html))
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
        self.assertTrue(b"874" in grab.doc.body)

    def test_charset_html5(self):
        grab = Grab()
        grab.setup_document(b"<meta charset='cp1251'>")
        self.assertEqual("cp1251", grab.doc.charset)

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
