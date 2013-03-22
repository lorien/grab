# coding: utf-8
from unittest import TestCase

import os
import sys
root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, root)

from grab.selector import Selector, TextSelector
from lxml.html import fromstring

HTML = """
<html>
    <body>
        <h1>test</h1>
        <ul>
            <li>one</li>
            <li>two</li>
            <li>three</li>
            <li id="6">z 4 foo</li>
        </ul>
        <ul id="second-list">
            <li class="li-1">yet one</li>
            <li class="li-2">yet two</li>
        </ul>
    </body>
</html>
"""

class TestSelector(TestCase):
    def setUp(self):
        self.tree = fromstring(HTML)

    def test_in_general(self):
        sel = Selector(self.tree)

    def test_select_node(self):
        self.assertEquals('test', Selector(self.tree).select('//h1')[0].node.text)

    def test_html(self):
        sel = Selector(self.tree.xpath('//h1')[0])
        self.assertEquals('<h1>test</h1>', sel.html().strip())

    def test_textselector(self):
        self.assertEquals('one', Selector(self.tree).select('//li/text()').text())

    def test_number(self):
        self.assertEquals(4, Selector(self.tree).select('//li[last()]').number())
        self.assertEquals(6, Selector(self.tree).select('//li[last()]/@id').number())

    def test_text_selector(self):
        sel = Selector(self.tree).select('//li/text()').one()
        self.assertTrue(isinstance(sel, TextSelector))

    # TODO: add --pyquery flag to runtest script
    #def test_select_pyquery(self):
        #root = Selector(self.tree)
        #self.assertEquals('test', root.select(pyquery='h1')[0].node.text)
        #self.assertEquals('z 4 foo', root.select(pyquery='body')[0].select(pyquery='#6')[0].node.text)

    def test_select_select(self):
        root = Selector(self.tree)
        self.assertEquals(set(['one', 'yet one']),
                          set([x.text() for x in root.select('//ul').select('./li[1]')]),
                          )

    def test_text_list(self):
        root = Selector(self.tree)
        self.assertEquals(set(['one', 'yet one']),
                          set(root.select('//ul/li[1]').text_list()),
                          )

    def test_attr_list(self):
        root = Selector(self.tree)
        self.assertEquals(set(['li-1', 'li-2']),
                          set(root.select('//ul[@id="second-list"]/li')\
                                  .attr_list('class'))
                          )


class TestSelectorList(TestCase):
    def setUp(self):
        self.tree = fromstring(HTML)

    def test_one(self):
        sel = Selector(self.tree).select('//ul/li')
        self.assertEquals('one', sel.one().node.text)
        self.assertEquals('one', sel.text())

    def test_number(self):
        sel = Selector(self.tree).select('//li[4]')
        self.assertEquals(4, sel.number())

    def test_exists(self):
        sel = Selector(self.tree).select('//li[4]')
        self.assertEquals(True, sel.exists())

        sel = Selector(self.tree).select('//li[5]')
        self.assertEquals(False, sel.exists())
