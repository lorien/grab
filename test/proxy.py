# coding: utf-8
from unittest import TestCase
#import string
import json
import re

from grab import Grab, GrabMisuseError
from .util import TMP_FILE, GRAB_TRANSPORT
from .tornado_util import SERVER

class ProxyTestCase(TestCase):
    def setUp(self):
        SERVER.reset()
        with open(TMP_FILE, 'w') as out:
            out.write('1.1.1.1:8080\n')
            out.write('1.1.1.2:8080\n')

    def test_basic(self):
        g = Grab(transport=GRAB_TRANSPORT)
        self.assertEqual(0, len(g.proxylist.proxy_list))

    def test_load(self):
        g = Grab(transport=GRAB_TRANSPORT)
        g.proxylist.set_source('file', location=TMP_FILE)
        self.assertEqual(2, len(g.proxylist.proxy_list))
