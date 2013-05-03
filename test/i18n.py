# coding: utf-8
from __future__ import absolute_import
from unittest import TestCase
from grab import Grab, DataNotFound, GrabMisuseError
import os.path

from .util import GRAB_TRANSPORT
from .tornado_util import SERVER

class TestResponse(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_idn(self):
        url = 'http://почта.рф/path?arg=val'
        idn_url = 'http://xn--80a1acny.xn--p1ai/path?arg=val'
        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(url=url)
        self.assertEqual(g.config['url'], idn_url)
