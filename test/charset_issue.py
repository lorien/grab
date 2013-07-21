# coding: utf-8
from unittest import TestCase
from grab import Grab, DataNotFound

from .util import GRAB_TRANSPORT
from .tornado_util import SERVER

from grab.util.py3k_support import *

class LXMLExtensionTest(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_dash_issue(self):
        HTML = '<strong>&#151;</strong>'
        SERVER.RESPONSE['get'] = HTML
        g = Grab()
        g.go(SERVER.BASE_URL)

        # By default &#[128-160]; are fixed
        self.assertFalse(g.xpath_one('//strong/text()') == unichr(151))
        self.assertTrue(g.xpath_one('//strong/text()') == unichr(8212))

        # disable fix-behaviour
        g.setup(fix_special_entities=False)
        g.go(SERVER.BASE_URL)

        # By default &#[128-160]; are fixed
        self.assertTrue(g.xpath_one('//strong/text()') == unichr(151))
        self.assertFalse(g.xpath_one('//strong/text()') == unichr(8212))

        # Explicitly use unicode_body func
        g = Grab()
        g.go(SERVER.BASE_URL)
        print(':::', g.response.unicode_body())
        self.assertTrue('&#8212;' in g.response.unicode_body())
