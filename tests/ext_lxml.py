from grab import DataNotFound
from grab.util import warning
from test_server import Response
from tests.util import BaseGrabTestCase, build_grab

HTML = """
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
"""


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
        warning.DISABLE_WARNINGS = True
        super(LXMLExtensionTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        warning.DISABLE_WARNINGS = False
        super(LXMLExtensionTest, cls).tearDownClass()

    def setUp(self):
        self.server.reset()

        # Create fake grab instance with fake response
        self.grab = build_grab()
        self.grab.setup_document(HTML.encode("cp1251"), charset="cp1251")

        from lxml.html import fromstring  # pylint: disable=import-outside-toplevel

        self.lxml_tree = fromstring(self.grab.doc.body)

    def test_lxml_text_content_fail(self):
        # lxml node text_content() method do not put spaces between text
        # content of adjacent XML nodes
        self.assertEqual(
            self.lxml_tree.xpath('//div[@id="bee"]/div')[0].text_content().strip(),
            "пчела",
        )
        self.assertEqual(
            self.lxml_tree.xpath('//div[@id="fly"]')[0].text_content().strip(),
            "му\nха",
        )

    def test_lxml_xpath(self):
        names = set(x.tag for x in self.lxml_tree.xpath('//div[@id="bee"]//*'))
        self.assertEqual(set(["em", "div", "strong", "style", "script"]), names)
        xpath_query = '//div[@id="bee"]//*[name() != "script" and name() != "style"]'
        names = set(x.tag for x in self.lxml_tree.xpath(xpath_query))
        self.assertEqual(set(["em", "div", "strong"]), names)

    def test_xpath(self):
        self.assertEqual("bee-em", self.grab.doc.select("//em").node().get("id"))
        ####self.grab.xpath_one('//em')
        self.assertEqual(
            "num-2", self.grab.doc.select('//*[text() = "item #2"]').node().get("id")
        )
        self.assertRaises(
            DataNotFound, lambda: self.grab.doc.select('//em[@id="baz"]').node()
        )
        self.assertEqual(None, self.grab.doc.select("//zzz").node(default=None))
        self.assertEqual("foo", self.grab.doc.select("//zzz").node(default="foo"))

    def test_xpath_text(self):
        self.assertEqual(
            "пче ла", self.grab.doc.select('//*[@id="bee"]').text(smart=True)
        )
        self.assertEqual(
            "пчела mozilla = 777; body { color: green; }",
            self.grab.doc.select('//*[@id="bee"]').text(smart=False),
        )
        self.assertEqual(
            "пче ла му ха item #100 2 item #2",
            self.grab.doc.select("/html/body").text(smart=True),
        )
        self.assertRaises(DataNotFound, lambda: self.grab.doc("//code").text())
        self.assertEqual("bee", self.grab.doc.select('//*[@id="bee"]/@id').text())
        self.assertRaises(
            DataNotFound, lambda: self.grab.doc.select('//*[@id="bee2"]/@id').text()
        )

    def test_xpath_number(self):
        self.assertEqual(100, self.grab.doc.select("//li").number())
        self.assertEqual(100, self.grab.doc.select("//li").number(make_int=True))
        self.assertEqual("100", self.grab.doc.select("//li").number(make_int=False))
        self.assertEqual(1002, self.grab.doc.select("//li").number(ignore_spaces=True))
        self.assertEqual(
            "1002",
            self.grab.doc.select("//li").number(ignore_spaces=True, make_int=False),
        )
        self.assertRaises(DataNotFound, lambda: self.grab.doc.select("//liza").number())
        self.assertEqual("foo", self.grab.doc.select("//zzz").number(default="foo"))

    def test_xpath_list(self):
        self.assertEqual(
            ["num-1", "num-2"],
            [x.get("id") for x in self.grab.doc.select("//li").node_list()],
        )

    def test_css_list(self):
        self.assertEqual(
            ["num-1", "num-2"],
            [x.get("id") for x in self.grab.doc.tree.cssselect("li")],
        )

    def test_xpath_exists(self):
        self.assertTrue(self.grab.doc.select('//li[@id="num-1"]').exists())
        self.assertFalse(self.grab.doc.select('//li[@id="num-3"]').exists())

    def test_cdata_issue(self):
        self.server.add_response(Response(data=XML), count=2)

        # By default HTML DOM builder is used
        # It handles CDATA incorrectly
        # Date: Dec 8, 2022 starts
        # Comment: It does not loose data anymore
        # grab = build_grab()
        # grab.go(self.server.get_url())
        # self.assertEqual(None, grab.doc.select("//weight").node().text)
        # self.assertEqual(None, grab.doc.tree.xpath("//weight")[0].text)
        # Update Dec 8, 2022 ends

        # But XML DOM builder produces valid result
        # self.assertEqual(None, grab.xpath_one('//weight').text)
        grab = build_grab(content_type="xml")
        grab.go(self.server.get_url())
        self.assertEqual("30", grab.doc.tree.xpath("//weight")[0].text)

        # Use `content_type` option to change default DOM builder
        # grab = build_grab()
        # grab.fake_response(XML)
        # grab.setup(content_type='xml')
        # self.assertEqual('30', grab.xpath_one('//weight').text)
        # self.assertEqual('30', grab.tree.xpath('//weight')[0].text)

    def test_xml_declaration(self):
        """
        HTML with XML declaration should be processed without errors.
        """
        self.server.add_response(
            Response(
                data=(
                    b'<?xml version="1.0" encoding="UTF-8"?>'
                    b"<html><body><h1>test</h1></body></html>"
                )
            )
        )
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertEqual("test", grab.doc.select("//h1").text())

    def test_empty_document(self):
        self.server.add_response(Response(data=b"oops"))
        grab = build_grab()
        grab.go(self.server.get_url())
        grab.doc.select("//anytag").exists()

        self.server.add_response(Response(data=b"<frameset></frameset>"))
        grab = build_grab()
        grab.go(self.server.get_url())
        grab.doc.select("//anytag").exists()
