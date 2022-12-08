from tests.util import BaseGrabTestCase


class GrabApiTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_urllib3_idna_error(self):
        # pylint: disable=import-outside-toplevel
        from urllib3 import PoolManager

        # pylint: enable=import-outside-toplevel

        invalid_url = (
            "http://13354&altProductId=6423589&productId=6423589"
            "&altProductStoreId=13713&catalogId=10001"
            "&categoryId=28678&productStoreId=13713"
            "http://www.textbooksnow.com/webapp/wcs/stores"
            "/servlet/ProductDisplay?langId=-1&storeId="
        )
        pool = PoolManager()
        self.assertRaises(UnicodeError, pool.request, "GET", invalid_url, retries=False)
