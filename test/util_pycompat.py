from unittest import TestCase
import sys

from grab.util import py3k_support


class PyCompatTestCase(TestCase):
    def test_py3k_support_py3k(self):
        if sys.version_info[0] > 2:
            self.assertTrue(py3k_support.PY3K)
        else:
            self.assertFalse(py3k_support.PY3K)

    def test_py3k_support_alias(self):
        if sys.version_info[0] > 2:
            self.assertEqual(py3k_support.xrange, range)
            self.assertEqual(py3k_support.basestring, str)
            self.assertEqual(py3k_support.unicode, str)
            self.assertEqual(py3k_support.unichr, chr)
            self.assertEqual(py3k_support.raw_input, input)
