# coding: utf-8
from unittest import TestCase
import os

from grab import Grab, GrabMisuseError
from .util import BASE_URL,  GRAB_TRANSPORT
from .tornado_util import REQUEST


class TestFlask(TestCase):
    def test_flask(self):
        g = Grab(transport=GRAB_TRANSPORT)
        g.go(BASE_URL + '?foo=4')
        self.assertEqual(REQUEST['args']['foo'], '4')

    def test_flask2(self):
        g = Grab(transport=GRAB_TRANSPORT)
        g.go(BASE_URL + '?foo=5')
        self.assertEqual(REQUEST['args']['foo'], '5')
