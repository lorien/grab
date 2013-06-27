# coding: utf-8
from unittest import TestCase
from lxml.html import fromstring
from grab.tools.lxml_tools import (get_node_text, find_node_number, render_html,
                                   drop_node, replace_node_with_text)

HTML = u"""
<head>
    <title>фыва</title>
    <meta http-equiv="Content-Type" content="text/html; charset=cp1251" />
</head>
<body>
    <div id="bee">
        <div class="wrapper">
            <strong id="bee-strong">пче</strong><em id="bee-em">ла</em>
        </div>
        <script type="text/javascript">
        mozilla = 777;
        </script>
        <style type="text/css">
        body { color: green; }
        </style>
    </div>
    <div id="fly">
        <strong id="fly-strong">му\n</strong><em id="fly-em">ха</em>
    </div>
    <ul id="num">
        <li id="num-1">item #100 2</li>
        <li id="num-2">item #2</li>
    </ul>
""".encode('cp1251')

class LXMLToolsTest(TestCase):
    def setUp(self):
        self.lxml_tree = fromstring(HTML)

    def test_get_node_text(self):
        elem = self.lxml_tree.xpath('//div[@id="bee"]')[0]
        self.assertEqual(get_node_text(elem), u'пчела mozilla = 777; body { color: green; }')
        self.assertEqual(get_node_text(elem, smart=True), u'пче ла')
        elem = self.lxml_tree.xpath('//div[@id="fly"]')[0]
        self.assertEqual(get_node_text(elem), u'му ха')

    def test_find_node_number(self):
        node = self.lxml_tree.xpath('//li[@id="num-1"]')[0]
        self.assertEqual(100, find_node_number(node))
        self.assertEqual('100', find_node_number(node, make_int=False))
        self.assertEqual(1002, find_node_number(node, ignore_spaces=True))

    def test_render_html(self):
        html = u'<html><body><p>фыва</p></body></html>'
        html_utf = html.encode('utf-8')
        tree = fromstring(html)
        self.assertEqual(html_utf, render_html(tree))
        self.assertEqual(html, render_html(tree, make_unicode=True))
        self.assertEqual(html.encode('cp1251'), render_html(tree, encoding='cp1251'))

    def test_drop_node(self):
        HTML = """
            <div><p>text<span>span</span><a href="#">link</a></p>tail</div>"""
        tree = fromstring(HTML)
        drop_node(tree, './/p')
        self.assertTrue(render_html(tree) == b'<div>tail</div>')

        tree = fromstring(HTML)
        drop_node(tree, './/span', keep_content=True)
        self.assertTrue(render_html(tree) == b'<div><p>textspan<a href="#">link</a></p>tail</div>')

    def test_replace_node_with_text(self):
        # replace span
        HTML = """
            <div><p><span>span</span><a href="#">link</a></p></div>"""
        tree = fromstring(HTML)
        replace_node_with_text(tree, './/span', 'FOO')
        self.assertTrue(render_html(tree) == b'<div><p>FOO<a href="#">link</a></p></div>')

        # replace span and keep its tail
        HTML = """
            <div><p><span>span</span>BAR<a href="#">link</a></p></div>"""
        tree = fromstring(HTML)
        replace_node_with_text(tree, './/span', 'FOO')
        self.assertTrue(render_html(tree) == b'<div><p>FOOBAR<a href="#">link</a></p></div>')

        # replace p which is only child of parent div
        HTML = """
            <div><p><span>span</span>BAR<a href="#">link</a></p></div>"""
        tree = fromstring(HTML)
        replace_node_with_text(tree, './/p', 'FOO')
        self.assertTrue(render_html(tree) == b'<div>FOO</div>')

        # replace span and keep tai of its preceeding sibling element
        HTML = """
            <div><p><strong>str</strong>!<span>span</span>BAR<a href="#">link</a></p></div>"""
        tree = fromstring(HTML)
        replace_node_with_text(tree, './/span', 'FOO')
        self.assertTrue(render_html(tree) == b'<div><p><strong>str</strong>!FOOBAR<a href="#">link</a></p></div>')
