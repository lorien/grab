# coding: utf-8
from unittest import TestCase
from lxml.html import fromstring
from grab.tools.lxml_tools import get_node_text, find_node_number

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
        self.assertEqual(get_node_text(elem), u'пче ла')
        elem = self.lxml_tree.xpath('//div[@id="fly"]')[0]
        self.assertEqual(get_node_text(elem), u'му ха')

    def test_find_node_number(self):
        node = self.lxml_tree.xpath('//li[@id="num-1"]')[0]
        self.assertEqual('100', find_node_number(node))
        self.assertEqual('1002', find_node_number(node, ignore_spaces=True))
