from unittest import TestCase

from urllib3.exceptions import ConnectTimeoutError

from grab import GrabNetworkError, request
from tests.util import NON_ROUTABLE_IP


class GrabErrorTestCase(TestCase):
    def test_original_exceptions_urllib2(self) -> None:
        try:
            request("http://%s" % NON_ROUTABLE_IP, timeout=1)
        except GrabNetworkError as ex:
            self.assertTrue(isinstance(ex.original_exc, ConnectTimeoutError))
