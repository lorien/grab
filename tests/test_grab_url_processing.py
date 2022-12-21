from urllib.parse import quote

from test_server import Response

from grab.error import GrabError
from tests.util import BaseGrabTestCase, build_grab


class GrabUrlProcessingTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_nonascii_path(self):
        grab = build_grab()
        self.server.add_response(Response(data=b"medved"))
        url = self.server.get_url("/превед?foo=bar")
        grab.request(url)
        self.assertEqual(b"medved", grab.doc.body)
        self.assertEqual(
            "/%D0%BF%D1%80%D0%B5%D0%B2%D0%B5%D0%B4",
            # u'/превед',
            self.server.request.path,
        )

    def test_nonascii_query(self):
        grab = build_grab()
        self.server.add_response(Response(data=b"medved"))
        grab.request(self.server.get_url("/search?q=превед"))
        self.assertEqual(b"medved", grab.doc.body)
        self.assertEqual("превед", self.server.request.args["q"])

    def test_null_byte_url(self):
        redirect_url = self.server.get_url().rstrip("/") + "/\x00/"
        self.server.add_response(
            Response(status=302, data=b"x", headers=[("Location", redirect_url)])
        )
        self.server.add_response(Response(data=b"y"))
        grab = build_grab()
        grab.request(self.server.get_url())
        self.assertEqual(b"y", grab.doc.body)
        self.assertEqual(grab.doc.url, quote(redirect_url, safe=":./?&"))

    def test_urllib3_idna_error(self):
        invalid_url = (
            "http://13354&altProductId=6423589&productId=6423589"
            "&altProductStoreId=13713&catalogId=10001"
            "&categoryId=28678&productStoreId=13713"
            "http://www.textbooksnow.com/webapp/wcs/stores"
            "/servlet/ProductDisplay?langId=-1&storeId="
        )
        grab = build_grab()
        with self.assertRaises(GrabError) as ex:
            grab.request(invalid_url)
        self.assertTrue("Failed to parse" in str(ex.exception))
