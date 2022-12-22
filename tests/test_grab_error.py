from unittest import TestCase

from urllib3.exceptions import ConnectTimeoutError

from grab import GrabNetworkError
from tests.util import NON_ROUTABLE_IP, build_grab


class GrabErrorTestCase(TestCase):
    def test_original_exceptions_urllib2(self):
        grab = build_grab()
        try:
            grab.request("http://%s" % NON_ROUTABLE_IP, timeout=1)
        except GrabNetworkError as ex:
            self.assertTrue(isinstance(ex.original_exc, ConnectTimeoutError))
