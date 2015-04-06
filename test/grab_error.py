from unittest import TestCase
import mock
from six import StringIO

from grab.error import warn

class GrabErrorTestCase(TestCase):
    def test_warn(self):
        out = StringIO()
        with mock.patch('sys.stderr', out):
            warn('abc')
        self.assertTrue('GrabDeprecationWarning: abc' in out.getvalue())
