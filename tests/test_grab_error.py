from unittest import TestCase

from urllib3.exceptions import ConnectTimeoutError

from grab import GrabNetworkError
from tests.util import NON_ROUTABLE_IP, build_grab


class GrabErrorTestCase(TestCase):
    # FIXME: does not work with pytest capturing
    # def test_warn(self):
    #    out = StringIO()
    #    with mock.patch("sys.stderr", out):
    #        warn("abc")
    #    self.assertTrue("GrabDeprecationWarning: abc" in out.getvalue())

    def test_original_exceptions_urllib2(self):

        grab = build_grab()
        try:
            grab.go("http://%s" % NON_ROUTABLE_IP)
        except GrabNetworkError as ex:
            self.assertTrue(isinstance(ex.original_exc, ConnectTimeoutError))

    def test_attribute_exception(self):
        grab = build_grab()
        self.assertTrue(grab.exception is None)
        with self.assertRaises(GrabNetworkError):
            grab.go("http://%s" % NON_ROUTABLE_IP)
