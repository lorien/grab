# coding: utf-8
from tests.util import BaseGrabTestCase, only_grab_transport


class GrabApiTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    @only_grab_transport('urllib3')
    def test_urllib3_idna_error(self):
        invalid_url = (
            'http://13354&altProductId=6423589&productId=6423589'
            '&altProductStoreId=13713&catalogId=10001'
            '&categoryId=28678&productStoreId=13713'
            'http://www.textbooksnow.com/webapp/wcs/stores'
            '/servlet/ProductDisplay?langId=-1&storeId='
        )
        from urllib3 import PoolManager
        from urllib3.exceptions import NewConnectionError
        pool = PoolManager()
        self.assertRaises(
            UnicodeError, pool.request, 'GET', invalid_url,
            retries=False
        )
