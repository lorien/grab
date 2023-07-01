from urllib3 import PoolManager
from urllib3.exceptions import LocationParseError

from grab import request
from grab.errors import GrabInvalidResponseError
from tests.util import BaseTestCase


class GrabApiTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    def test_urllib3_idna_error(self) -> None:
        # It was failed with UnicodeError on previuos
        # versions of python or ullib3 library
        # I do not remember clearly.
        # Now it produces valid exception

        invalid_url = (
            "http://13354&altProductId=6423589&productId=6423589"
            "&altProductStoreId=13713&catalogId=10001"
            "&categoryId=28678&productStoreId=13713"
            "http://www.textbooksnow.com/webapp/wcs/stores"
            "/servlet/ProductDisplay?langId=-1&storeId="
        )
        pool = PoolManager()
        self.assertRaises(
            LocationParseError, pool.request, "GET", invalid_url, retries=False
        )

    def test_invalid_url(self) -> None:
        invalid_url = (
            "http://13354&altProductId=6423589&productId=6423589"
            "&altProductStoreId=13713&catalogId=10001"
            "&categoryId=28678&productStoreId=13713"
            "http://www.textbooksnow.com/webapp/wcs/stores"
            "/servlet/ProductDisplay?langId=-1&storeId="
        )
        with self.assertRaises(GrabInvalidResponseError):
            request(invalid_url)
