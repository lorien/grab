from io import StringIO
from unittest import TestCase

import mock

from grab import GrabNetworkError
from grab.util.warning import warn
from tests.util import NON_ROUTABLE_IP, build_grab


class GrabErrorTestCase(TestCase):
    def test_warn(self):
        out = StringIO()
        with mock.patch("sys.stderr", out):
            warn("abc")
        self.assertTrue("GrabDeprecationWarning: abc" in out.getvalue())

    def test_original_exceptions_urllib2(self):
        from urllib3.exceptions import (  # pylint: disable=import-outside-toplevel
            ConnectTimeoutError,
        )

        grab = build_grab()
        try:
            grab.go("http://%s" % NON_ROUTABLE_IP)
        except GrabNetworkError as ex:  # pylint: disable=broad-except
            self.assertTrue(isinstance(ex.original_exc, ConnectTimeoutError))

    def test_attribute_exception(self):
        grab = build_grab()
        self.assertTrue(grab.exception is None)
        try:
            grab.go("http://%s" % NON_ROUTABLE_IP)
        except GrabNetworkError:
            pass
        self.assertTrue(isinstance(grab.exception, GrabNetworkError))
