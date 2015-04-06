# coding: utf-8
import six

from test.util import build_grab
from test.util import BaseGrabTestCase


class LXMLExtensionTest(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_dash_issue(self):
        HTML = '<strong>&#151;</strong>'
        self.server.response['get.data'] = HTML
        g = build_grab()
        g.go(self.server.get_url())

        # By default &#[128-160]; are fixed
        self.assertFalse(g.xpath_one('//strong/text()') == six.unichr(151))
        self.assertTrue(g.xpath_one('//strong/text()') == six.unichr(8212))

        # disable fix-behaviour
        g.setup(fix_special_entities=False)
        g.go(self.server.get_url())

        # By default &#[128-160]; are fixed
        self.assertTrue(g.xpath_one('//strong/text()') == six.unichr(151))
        self.assertFalse(g.xpath_one('//strong/text()') == six.unichr(8212))

        # Explicitly use unicode_body func
        g = build_grab()
        g.go(self.server.get_url())
        print(':::', g.response.unicode_body())
        self.assertTrue('&#8212;' in g.response.unicode_body())
