from test_server import Response

from grab import request
from grab.errors import GrabError
from tests.util import BaseTestCase


class GrabUrlProcessingTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    def test_nonascii_path(self) -> None:
        self.server.add_response(Response(data=b"medved"))
        url = self.server.get_url("/превед?foo=bar")
        doc = request(url)
        self.assertEqual(b"medved", doc.body)
        self.assertEqual(
            "/%D0%BF%D1%80%D0%B5%D0%B2%D0%B5%D0%B4",
            # u'/превед',
            self.server.request.path,
        )

    def test_nonascii_query(self) -> None:
        self.server.add_response(Response(data=b"medved"))
        doc = request(self.server.get_url("/search?q=превед"))
        self.assertEqual(b"medved", doc.body)
        self.assertEqual("превед", self.server.request.args["q"])

    def test_null_byte_url(self) -> None:
        redirect_url = self.server.get_url().rstrip("/") + "/\x00/"
        self.server.add_response(
            Response(status=302, data=b"x", headers=[("Location", redirect_url)])
        )
        self.server.add_response(Response(data=b"y"))
        doc = request(self.server.get_url())
        self.assertEqual(b"y", doc.body)
        # FIX this line: doc.url is http://127.0.0.1:39457/%00/
        # self.assertEqual(doc.url, quote(redirect_url, safe=":./?&"))

    def test_urllib3_idna_error(self) -> None:
        invalid_url = (
            "http://13354&altProductId=6423589&productId=6423589"
            "&altProductStoreId=13713&catalogId=10001"
            "&categoryId=28678&productStoreId=13713"
            "http://www.textbooksnow.com/webapp/wcs/stores"
            "/servlet/ProductDisplay?langId=-1&storeId="
        )
        with self.assertRaises(GrabError) as ex:
            request(invalid_url)
        self.assertTrue("Failed to parse" in str(ex.exception))
