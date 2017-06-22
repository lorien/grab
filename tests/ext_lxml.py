# coding: utf-8
from grab import DataNotFound

from tests.util import build_grab
from tests.util import BaseGrabTestCase

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


XML = b"""
<root>
    <man>
        <age>25</age>
        <weight><![CDATA[30]]></weight>
    </man>
</root>
"""


class LXMLExtensionTest(BaseGrabTestCase):
    @classmethod
    def setUpClass(cls):
        import grab.util.warning

        grab.util.warning.DISABLE_WARNINGS = True
        super(LXMLExtensionTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        import grab.util.warning

        grab.util.warning.DISABLE_WARNINGS = False
        super(LXMLExtensionTest, cls).tearDownClass()

    def setUp(self):
        self.server.reset()

        # Create fake grab instance with fake response
        self.grab = build_grab()
        self.grab.setup_document(HTML, charset='cp1251')

        from lxml.html import fromstring
        self.lxml_tree = fromstring(self.grab.doc.body)

    def test_lxml_text_content_fail(self):
        # lxml node text_content() method do not put spaces between text
        # content of adjacent XML nodes
        self.assertEqual(self.lxml_tree.xpath('//div[@id="bee"]/div')[0]
                         .text_content().strip(), u'пчела')
        self.assertEqual(self.lxml_tree.xpath('//div[@id="fly"]')[0]
                         .text_content().strip(), u'му\nха')

    def test_lxml_xpath(self):
        names = set(x.tag for x in self.lxml_tree.xpath('//div[@id="bee"]//*'))
        self.assertEqual(set(['em', 'div', 'strong',
                              'style', 'script']), names)
        xpath_query = '//div[@id="bee"]//*[name() != "script" and '\
                      'name() != "style"]'
        names = set(x.tag for x in self.lxml_tree.xpath(xpath_query))
        self.assertEqual(set(['em', 'div', 'strong']), names)

    def test_xpath(self):
        self.assertEqual('bee-em', self.grab.xpath_one('//em').get('id'))
        ####self.grab.xpath_one('//em')
        self.assertEqual('num-2',
                         self.grab.xpath_one(u'//*[text() = "item #2"]')
                         .get('id'))
        self.assertRaises(DataNotFound, self.grab.xpath_one, '//em[@id="baz"]')
        self.assertEqual(None, self.grab.xpath_one('//zzz', default=None))
        self.assertEqual('foo', self.grab.xpath_one('//zzz', default='foo'))

    def test_xpath_text(self):
        self.assertEqual(u'пче ла',
                         self.grab.xpath_text('//*[@id="bee"]', smart=True))
        self.assertEqual(u'пчела mozilla = 777; body { color: green; }',
                         self.grab.xpath_text('//*[@id="bee"]', smart=False))
        self.assertEqual(u'пче ла му ха item #100 2 item #2',
                         self.grab.xpath_text('/html/body', smart=True))
        self.assertRaises(DataNotFound, self.grab.xpath_text, '//code')
        self.assertEqual(u'bee', self.grab.xpath_one('//*[@id="bee"]/@id'))
        self.assertRaises(DataNotFound, self.grab.xpath_text,
                          '//*[@id="bee2"]/@id')

    def test_xpath_number(self):
        self.assertEqual(100, self.grab.xpath_number('//li'))
        self.assertEqual(100, self.grab.xpath_number('//li', make_int=True))
        self.assertEqual('100', self.grab.xpath_number('//li', make_int=False))
        self.assertEqual(1002, self.grab.xpath_number('//li',
                                                      ignore_spaces=True))
        self.assertEqual('1002', self.grab.xpath_number(
            '//li', ignore_spaces=True, make_int=False))
        self.assertRaises(DataNotFound, self.grab.xpath_number, '//liza')
        self.assertEqual('foo', self.grab.xpath_number('//zzz', default='foo'))

    def test_xpath_list(self):
        self.assertEqual(['num-1', 'num-2'],
                         [x.get('id') for x in self.grab.xpath_list('//li')])

    def test_css(self):
        self.assertEqual('bee-em', self.grab.css_one('em').get('id'))
        self.assertEqual('num-2', self.grab.css_one('#num-2').get('id'))
        self.assertRaises(DataNotFound, self.grab.css_one, 'em#baz')
        self.assertEqual('foo', self.grab.css_one('zzz', default='foo'))

    def test_css_text(self):
        self.assertEqual(u'пче ла', self.grab.css_text('#bee', smart=True))
        self.assertEqual(u'пче ла му ха item #100 2 item #2',
                         self.grab.css_text('html body', smart=True))
        self.assertRaises(DataNotFound, self.grab.css_text, 'code')
        self.assertEqual('foo', self.grab.css_text('zzz', default='foo'))

    def test_css_number(self):
        self.assertEqual(100, self.grab.css_number('li'))
        self.assertEqual('100', self.grab.css_number('li', make_int=False))
        self.assertEqual(1002, self.grab.css_number('li', ignore_spaces=True))
        self.assertRaises(DataNotFound, self.grab.css_number, 'liza')
        self.assertEqual('foo', self.grab.css_number('zzz', default='foo'))

    def test_css_list(self):
        self.assertEqual(['num-1', 'num-2'],
                         [x.get('id') for x in self.grab.css_list('li')])

    def test_strip_tags(self):
        self.assertEqual('foo', self.grab.strip_tags('<b>foo</b>'))
        self.assertEqual('foo bar', self.grab.strip_tags('<b>foo</b> <i>bar'))
        self.assertEqual('foobar', self.grab.strip_tags('<b>foo</b><i>bar'))
        self.assertEqual('foo bar',
                         self.grab.strip_tags('<b>foo</b><i>bar', smart=True))
        self.assertEqual('', self.grab.strip_tags('<b> <div>'))

    def test_css_exists(self):
        self.assertTrue(self.grab.css_exists('li#num-1'))
        self.assertFalse(self.grab.css_exists('li#num-3'))

    def test_xpath_exists(self):
        self.assertTrue(self.grab.xpath_exists('//li[@id="num-1"]'))
        self.assertFalse(self.grab.xpath_exists('//li[@id="num-3"]'))

    def test_cdata_issue(self):
        self.server.response['data'] = XML

        # By default HTML DOM builder is used
        # It handles CDATA incorrectly
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertEqual(None, grab.xpath_one('//weight').text)
        self.assertEqual(None, grab.doc.tree.xpath('//weight')[0].text)

        # But XML DOM builder produces valid result
        # self.assertEqual(None, grab.xpath_one('//weight').text)
        grab = build_grab(content_type='xml')
        grab.go(self.server.get_url())
        self.assertEqual('30', grab.doc.tree.xpath('//weight')[0].text)

        # Use `content_type` option to change default DOM builder
        #grab = build_grab()
        #grab.fake_response(XML)
        #grab.setup(content_type='xml')
        #self.assertEqual('30', grab.xpath_one('//weight').text)
        #self.assertEqual('30', grab.tree.xpath('//weight')[0].text)

    def test_xml_declaration(self):
        """
        HTML with XML declaration shuld be processed without errors.
        """
        self.server.response['get.data'] = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<html><body><h1>test</h1></body></html>'
        )
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertEqual('test', grab.xpath_text('//h1'))

    def test_empty_document(self):
        self.server.response['get.data'] = 'oops'
        grab = build_grab()
        grab.go(self.server.get_url())
        grab.xpath_exists('//anytag')

        self.server.response['get.data'] = '<frameset></frameset>'
        grab = build_grab()
        grab.go(self.server.get_url())
        grab.xpath_exists('//anytag')
