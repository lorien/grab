# coding: utf-8
from unittest import TestCase

#import os
#import sys
#root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
#sys.path.insert(0, root)

from test.util import GRAB_TRANSPORT, ignore_transport, only_transport
from test.server import SERVER
from grab.selector import KitSelector
from grab import Grab

from grab.util.py3k_support import *

HTML = """
<html>
    <body>
        <h1>test</h1>
        <ul>
            <li>one</li>
            <li>two</li>
            <li>three</li>
            <li class="zzz" id="6">z 4 foo</li>
        </ul>
        <ul id="second-list">
            <li class="li-1">yet one</li>
            <li class="li-2">yet two</li>
        </ul>
    </body>
</html>
"""

class KitSelectorTestCase(TestCase):
    def setUp(self):
        g = Grab(transport='grab.transport.kit.KitTransport')
        SERVER.RESPONSE['get'] = HTML
        g.go(SERVER.BASE_URL)
        self.qt_doc = g.transport.kit.page.mainFrame().documentElement()

    def test_in_general(self):
        sel = KitSelector(self.qt_doc)

    def test_select_node(self):
        sel = KitSelector(self.qt_doc).select('h1')[0]
        self.assertEquals('test', sel.node.toInnerXml())

    def test_html(self):
        sel = KitSelector(self.qt_doc).select('h1')[0]
        self.assertEquals('<h1>test</h1>', sel.html())

    def test_textselector(self):
        self.assertEquals('one', KitSelector(self.qt_doc).select('li').text())

    def test_number(self):
        self.assertEquals(4, KitSelector(self.qt_doc).select('li.zzz').number())

    # TODO
    # test the ID selector (#6)

    #def test_text_selector(self):
        #sel = KitSelector(self.qt_doc).select('//li/text()').one()
        #self.assertTrue(isinstance(sel, TextSelector))

    ## TODO: add --pyquery flag to runtest script
    ##def test_select_pyquery(self):
        ##root = Selector(self.qt_doc)
        ##self.assertEquals('test', root.select(pyquery='h1')[0].node.text)
        ##self.assertEquals('z 4 foo', root.select(pyquery='body')[0].select(pyquery='#6')[0].node.text)

    def test_select_select(self):
        root = KitSelector(self.qt_doc)
        self.assertEquals(set(['one', 'yet one']),
                          set([x.text() for x in root.select('ul').select('li:first-child')]),
                          )

    def test_text_list(self):
        root = KitSelector(self.qt_doc)
        self.assertEquals(set(['one', 'yet one']),
                          set(root.select('ul > li:first-child').text_list()),
                          )

    def test_attr_list(self):
        root = KitSelector(self.qt_doc)
        self.assertEquals(set(['li-1', 'li-2']),
                          set(root.select('ul[id=second-list] > li')\
                                  .attr_list('class'))
                          )


class TestSelectorList(TestCase):
    def setUp(self):
        g = Grab(transport='grab.transport.kit.KitTransport')
        SERVER.RESPONSE['get'] = HTML
        g.go(SERVER.BASE_URL)
        self.qt_doc = g.transport.kit.page.mainFrame().documentElement()

    def test_one(self):
        sel = KitSelector(self.qt_doc).select('ul > li')
        self.assertEquals('one', unicode(sel.one().node.toPlainText()))
        self.assertEquals('one', sel.text())

    def test_number(self):
        sel = KitSelector(self.qt_doc).select('li:nth-child(4)')
        self.assertEquals(4, sel.number())

    def test_exists(self):
        sel = KitSelector(self.qt_doc).select('li:nth-child(4)')
        self.assertEquals(True, sel.exists())

        sel = KitSelector(self.qt_doc).select('li:nth-child(5)')
        self.assertEquals(False, sel.exists())
