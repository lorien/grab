from __future__ import annotations

import typing
from typing import cast

from lxml.etree import _Element
from lxml.html import HtmlElement, fromstring
from test_server import Response

from grab import DataNotFound, request
from grab.document import Document
from tests.util import BaseTestCase

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


class LXMLExtensionTest(BaseTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

    def setUp(self) -> None:
        self.server.reset()

        # Create fake grab instance with fake response
        self.doc = Document(
            body=HTML.encode("cp1251"),
            encoding="cp1251",
        )
        self.lxml_tree = fromstring(self.doc.body)

    def test_lxml_text_content_fail(self) -> None:
        # lxml node text_content() method do not put spaces between text
        # content of adjacent XML nodes
        # pylint: disable=deprecated-typing-alias
        self.assertEqual(
            cast(
                typing.List[HtmlElement], self.lxml_tree.xpath('//div[@id="bee"]/div')
            )[0]
            .text_content()
            .strip(),
            "пчела",
        )
        self.assertEqual(
            cast(typing.List[HtmlElement], self.lxml_tree.xpath('//div[@id="fly"]'))[0]
            .text_content()
            .strip(),
            "му\nха",
        )

    def test_lxml_xpath(self) -> None:
        # pylint: disable=deprecated-typing-alias
        names = {
            x.tag
            for x in cast(
                typing.List[_Element], self.lxml_tree.xpath('//div[@id="bee"]//*')
            )
        }
        self.assertEqual({"em", "div", "strong", "style", "script"}, names)
        xpath_query = '//div[@id="bee"]//*[name() != "script" and name() != "style"]'
        names = {
            x.tag
            for x in cast(typing.List[_Element], self.lxml_tree.xpath(xpath_query))
        }
        self.assertEqual({"em", "div", "strong"}, names)

    def test_xpath(self) -> None:
        self.assertEqual("bee-em", self.doc.select("//em").node().get("id"))
        self.assertEqual(
            "num-2", self.doc.select('//*[text() = "item #2"]').node().get("id")
        )
        self.assertRaises(
            DataNotFound, lambda: self.doc.select('//em[@id="baz"]').node()
        )
        self.assertEqual(None, self.doc.select("//zzz").node(default=None))
        self.assertEqual("foo", self.doc.select("//zzz").node(default="foo"))

    def test_xpath_text(self) -> None:
        self.assertEqual("пче ла", self.doc.select('//*[@id="bee"]').text(smart=True))
        self.assertEqual(
            "пчела mozilla = 777; body { color: green; }",
            self.doc.select('//*[@id="bee"]').text(smart=False),
        )
        self.assertEqual(
            "пче ла му ха item #100 2 item #2",
            self.doc.select("/html/body").text(smart=True),
        )
        self.assertRaises(DataNotFound, lambda: self.doc.select("//code").text())
        self.assertEqual("bee", self.doc.select('//*[@id="bee"]/@id').text())
        self.assertRaises(
            DataNotFound, lambda: self.doc.select('//*[@id="bee2"]/@id').text()
        )

    def test_xpath_number(self) -> None:
        self.assertEqual(100, self.doc.select("//li").number())
        self.assertEqual(100, self.doc.select("//li").number(make_int=True))
        self.assertEqual("100", self.doc.select("//li").number(make_int=False))
        self.assertEqual(1002, self.doc.select("//li").number(ignore_spaces=True))
        self.assertEqual(
            "1002",
            self.doc.select("//li").number(ignore_spaces=True, make_int=False),
        )
        self.assertRaises(DataNotFound, lambda: self.doc.select("//liza").number())
        self.assertEqual("foo", self.doc.select("//zzz").number(default="foo"))

    def test_xpath_list(self) -> None:
        self.assertEqual(
            ["num-1", "num-2"],
            [x.get("id") for x in self.doc.select("//li").node_list()],
        )

    def test_css_list(self) -> None:
        self.assertEqual(
            ["num-1", "num-2"],
            [x.get("id") for x in self.doc.tree.cssselect("li")],
        )

    def test_xpath_exists(self) -> None:
        self.assertTrue(self.doc.select('//li[@id="num-1"]').exists())
        self.assertFalse(self.doc.select('//li[@id="num-3"]').exists())

    def test_cdata_issue(self) -> None:
        # pylint: disable=deprecated-typing-alias
        self.server.add_response(Response(data=XML), count=2)
        doc = request(self.server.get_url(), document_type="xml")
        self.assertEqual(
            "30", cast(typing.List[_Element], doc.tree.xpath("//weight"))[0].text
        )

    def test_xml_declaration(self) -> None:
        # HTML with XML declaration should be processed without errors.
        self.server.add_response(
            Response(
                data=(
                    b'<?xml version="1.0" encoding="UTF-8"?>'
                    b"<html><body><h1>test</h1></body></html>"
                )
            )
        )
        doc = request(self.server.get_url())
        self.assertEqual("test", doc.select("//h1").text())

    def test_empty_document(self) -> None:
        self.server.add_response(Response(data=b"oops"))
        doc = request(self.server.get_url())
        doc.select("//anytag").exists()

        self.server.add_response(Response(data=b"<frameset></frameset>"))
        doc = request(self.server.get_url())
        doc.select("//anytag").exists()
