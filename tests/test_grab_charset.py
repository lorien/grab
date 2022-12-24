from test_server import Response

from grab.document import Document
from tests.util import BaseGrabTestCase, build_grab


class GrabCharsetDetectionTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_encoding_option(self):
        grab = build_grab()
        self.server.add_response(Response(data=b"foo"))
        doc = grab.request(self.server.get_url())
        self.assertEqual(b"foo", doc.body)

        grab = build_grab()
        self.server.add_response(Response(data="фуу".encode("utf-8")))
        doc = grab.request(self.server.get_url())
        self.assertEqual("фуу".encode("utf-8"), doc.body)

        self.assertEqual(doc.encoding, "utf-8")

        grab = build_grab()
        self.server.add_response(Response(data="фуу".encode("cp1251")))
        doc = grab.request(self.server.get_url(), encoding="cp1251")
        self.assertEqual("фуу".encode("cp1251"), doc.body)
        self.assertEqual(doc.encoding, "windows-1251")  # normalized

    def test_encoding_lowercase(self):
        self.server.add_response(
            Response(headers=[("Content-Type", "text/html; charset=cp1251")])
        )
        grab = build_grab()
        doc = grab.request(self.server.get_url())
        self.assertEqual("windows-1251", doc.encoding)

    def test_dash2_issue(self):
        html = b"<strong>&#151;</strong>"
        self.server.add_response(Response(data=html))
        grab = build_grab()
        doc = grab.request(self.server.get_url())

        # By default &#[128-159]; are fixed
        self.assertFalse(doc.select("//strong/text()").text() == chr(151))
        self.assertTrue(doc.select("//strong/text()").text() == chr(8212))

    def test_invalid_charset(self):
        html = b"""<head><meta http-equiv="Content-Type"
                    content="text/html; charset=windows-874">'
                    </head><body>test</body>"""
        self.server.add_response(Response(data=html))
        grab = build_grab()
        doc = grab.request(self.server.get_url())
        self.assertTrue(b"874" in doc.body)

    def test_charset_html5(self):
        doc = Document(b"<meta charset='cp1251'>")
        self.assertEqual("windows-1251", doc.encoding)

        doc = Document(b"<meta charset='windows-1251'>")
        self.assertEqual("windows-1251", doc.encoding)

        doc = Document(b'<meta charset="windows-1252">')
        self.assertEqual("windows-1252", doc.encoding)

        doc = Document(b"<meta charset=latin-1>")
        self.assertEqual("latin-1", doc.encoding)

        doc = Document(b"<meta charset  =  'windows-1251'  >")
        self.assertEqual("windows-1251", doc.encoding)

        doc = Document(b'<meta charset  =  "windows-1252"   >')
        self.assertEqual("windows-1252", doc.encoding)

        doc = Document(b"<meta charset  =  latin-1  >")
        self.assertEqual("latin-1", doc.encoding)
