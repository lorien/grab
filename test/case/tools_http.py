# coding: utf-8
from __future__ import absolute_import
from unittest import TestCase
from grab import Grab, DataNotFound, GrabMisuseError
import os.path

from test.util import build_grab
from test.server import SERVER
from grab.tools.http import normalize_url

class TestResponse(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_idn(self):
        url = 'http://почта.рф/path?arg=val'
        idn_url = 'http://xn--80a1acny.xn--p1ai/path?arg=val'
        self.assertEqual(idn_url, normalize_url(url))
