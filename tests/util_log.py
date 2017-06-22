# coding: utf-8
from unittest import TestCase
import sys

from grab.util.log import PycurlSigintHandler


class PycurlSigintHandlerTestCase(TestCase):
    def test_record(self):
        handler = PycurlSigintHandler()
        with handler.record():
            sys.stderr.write('one-1')
            sys.stderr.write('two-2')
        val = handler.get_output()
        self.assertEqual('one-1two-2', val)
