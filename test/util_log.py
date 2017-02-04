# coding: utf-8
from unittest import TestCase
import sys

from grab.util.log import StderrProxy

class LogModuleTestCase(TestCase):
    def test_stderr_proxy(self):
        proxy = StderrProxy()
        with proxy.record():
            sys.stderr.write('one-1')
            sys.stderr.write('two-2')
        val = proxy.getvalue()
        self.assertEqual('one-1two-2', val)
