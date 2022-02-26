# coding: utf-8
from unittest import TestCase
import sys

from grab.util.log import PycurlSigintHandler, default_logging
from tests.util import temp_file


class PycurlSigintHandlerTestCase(TestCase):
    def test_record(self):
        handler = PycurlSigintHandler()
        with handler.record():
            sys.stderr.write("one-1")
            sys.stderr.write("two-2")
        val = handler.get_output()
        self.assertEqual("one-1two-2", val)

    def test_use_stderr(self):
        handler = PycurlSigintHandler()
        sys.stderr.write("FOO!")
        with handler.record():
            sys.stderr.write("BAR!")

    def test_default_logging(self):
        with temp_file() as grab_network_file:
            with temp_file() as grab_file:
                default_logging(network_log=grab_network_file, grab_log=grab_file)
