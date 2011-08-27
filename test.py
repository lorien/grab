#!/usr/bin/env python
# coding: utf-8
import unittest
import re

from grab import Grab, GrabMisuseError, DataNotFound

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

class TextExtensionTest(unittest.TestCase):
    def setUp(self):
        # Create fake grab instance with fake response
        self.g = Grab()
        self.g.response.body = HTML
        self.g.response.charset = 'cp1251'

    def test_search(self):
        self.assertTrue(self.g.search(u'фыва'.encode('cp1251'), byte=True))
        self.assertTrue(self.g.search(u'фыва'))
        self.assertFalse(self.g.search(u'фыва2'))

    def test_search_usage_errors(self):
        self.assertRaises(GrabMisuseError,
            lambda: self.g.search(u'фыва', byte=True))
        self.assertRaises(GrabMisuseError,
            lambda: self.g.search('фыва'))

    def test_search_rex(self):
        # Search unicode rex in unicode body - default case
        rex = re.compile(u'фыва', re.U)
        self.assertEqual(u'фыва', self.g.search_rex(rex).group(0))

        # Search non-unicode rex in byte-string body
        rex = re.compile(u'фыва'.encode('cp1251'))
        self.assertEqual(u'фыва'.encode('cp1251'), self.g.search_rex(rex, byte=True).group(0))

        # Search for non-unicode rex in unicode body shuld fail
        rex = re.compile('фыва')
        self.assertEqual(None, self.g.search_rex(rex))

        # Search for unicode rex in byte-string body shuld fail
        rex = re.compile(u'фыва', re.U)
        self.assertEqual(None, self.g.search_rex(rex, byte=True))

        # Search for unexesting fragment
        rex = re.compile(u'фыва2', re.U)
        self.assertEqual(None, self.g.search_rex(rex))

    def test_assert_substring(self):
        self.g.assert_substring(u'фыва')
        self.g.assert_substring(u'фыва'.encode('cp1251'), byte=True)
        self.assertRaises(DataNotFound,
            lambda: self.g.assert_substring(u'фыва2'))

    def test_assert_rex(self):
        self.g.assert_rex(re.compile(u'фыва'))
        self.g.assert_rex(re.compile(u'фыва'.encode('cp1251')), byte=True)
        self.assertRaises(DataNotFound,
            lambda: self.g.assert_rex(re.compile(u'фыва2')))

    def test_find_number(self):
        self.assertEqual('2', self.g.find_number('2'))
        self.assertEqual('2', self.g.find_number('foo 2 4 bar'))
        self.assertEqual('24', self.g.find_number('foo 2 4 bar', ignore_spaces=True))
        self.assertEqual('24', self.g.find_number(u'бешеный 2 4 барсук', ignore_spaces=True))
        self.assertRaises(DataNotFound,
            lambda: self.g.find_number('foo'))
        self.assertRaises(DataNotFound,
            lambda: self.g.find_number(u'фыва'))

    def test_drop_space(self):
        self.assertEqual('', self.g.drop_space(' '))
        self.assertEqual('f', self.g.drop_space(' f '))
        self.assertEqual('fb', self.g.drop_space(' f b '))
        self.assertEqual(u'триглаза', self.g.drop_space(u' тр и гла' + '\t' + '\n' + u' за '))


class LXMLExtensionTest(unittest.TestCase):
    def setUp(self):
        # Create fake grab instance with fake response
        self.g = Grab()
        self.g.response.body = HTML
        self.g.response.charset = 'cp1251'

        from lxml.html import fromstring
        self.lxml_tree = fromstring(self.g.response.body)

    def test_lxml_text_content_fail(self):
        # lxml node text_content() method do not put spaces between text
        # content of adjacent XML nodes
        self.assertEqual(self.lxml_tree.xpath('//div[@id="bee"]/div')[0].text_content().strip(), u'пчела')
        self.assertEqual(self.lxml_tree.xpath('//div[@id="fly"]')[0].text_content().strip(), u'му\nха')

    def test_lxml_xpath(self):
        names = set(x.tag for x in self.lxml_tree.xpath('//div[@id="bee"]//*'))
        self.assertEqual(set(['em', 'div', 'strong', 'style', 'script']), names)
        names = set(x.tag for x in self.lxml_tree.xpath('//div[@id="bee"]//*[name() != "script" and name() != "style"]'))
        self.assertEqual(set(['em', 'div', 'strong']), names)

    def test_get_node_text(self):
        elem = self.lxml_tree.xpath('//div[@id="bee"]')[0]
        self.assertEqual(self.g.get_node_text(elem), u'пче ла')
        elem = self.lxml_tree.xpath('//div[@id="fly"]')[0]
        self.assertEqual(self.g.get_node_text(elem), u'му ха')

    def test_find_node_number(self):
        node = self.lxml_tree.xpath('//li[@id="num-1"]')[0]
        self.assertEqual('100', self.g.find_node_number(node))

    def test_xpath(self):
        self.assertEqual('bee-em', self.g.xpath('//em').get('id'))
        self.assertEqual('num-2', self.g.xpath(u'//*[text() = "item #2"]').get('id'))
        self.assertRaises(DataNotFound,
            lambda: self.g.xpath('//em[@id="baz"]'))

    def test_xpath_text(self):
        self.assertEqual(u'пче ла', self.g.xpath_text('//*[@id="bee"]'))
        self.assertEqual(u'пче ла му ха item #100 2 item #2', self.g.xpath_text('/html/body'))
        self.assertRaises(DataNotFound,
            lambda: self.g.xpath_text('//code'))

    def test_xpath_number(self):
        self.assertEqual('100', self.g.xpath_number('//li'))
        self.assertEqual('1002', self.g.xpath_number('//li', ignore_spaces=True))
        self.assertRaises(DataNotFound,
            lambda: self.g.xpath_number('//liza'))

    def test_xpath_list(self):
        self.assertEqual(['num-1', 'num-2'],
            [x.get('id') for x in self.g.xpath_list('//li')])

    def test_css(self):
        self.assertEqual('bee-em', self.g.css('em').get('id'))
        self.assertEqual('num-2', self.g.css('#num-2').get('id'))
        self.assertRaises(DataNotFound,
            lambda: self.g.css('em#baz'))

    def test_css_text(self):
        self.assertEqual(u'пче ла', self.g.css_text('#bee'))
        self.assertEqual(u'пче ла му ха item #100 2 item #2', self.g.css_text('html body'))
        self.assertRaises(DataNotFound,
            lambda: self.g.css_text('code'))

    def test_css_number(self):
        self.assertEqual('100', self.g.css_number('li'))
        self.assertEqual('1002', self.g.css_number('li', ignore_spaces=True))
        self.assertRaises(DataNotFound,
            lambda: self.g.css_number('liza'))

    def test_css_list(self):
        self.assertEqual(['num-1', 'num-2'],
            [x.get('id') for x in self.g.css_list('li')])


if __name__ == '__main__':
    unittest.main()
