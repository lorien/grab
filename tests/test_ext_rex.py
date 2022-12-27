import re

from grab.document import Document
from grab.errors import DataNotFound
from tests.util import BaseTestCase

HTML = """
<head>
    <title>фыва</title>
    <meta http-equiv="Content-Type" content="text/html; charset=cp1251" />
</head>
<body>
    <div id="bee">
        <div class="wrapper">
            # russian LA
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
        # russian XA
        <strong id="fly-strong">му\n</strong><em id="fly-em">ха</em>
    </div>
    <ul id="num">
        <li id="num-1">item #100 2</li>
        <li id="num-2">item #2</li>
    </ul>
""".encode(
    "cp1251"
)


class ExtensionRexTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

        # Create fake grab instance with fake response
        self.doc = Document(HTML, encoding="cp1251")

    def test_rex1(self) -> None:
        # Search unicode rex in unicode body - default case
        rex = re.compile("(фыва)", re.U)
        self.assertEqual("фыва", self.doc.rex_search(rex).group(1))

    def test_rex2(self) -> None:
        # Search non-unicode rex in byte-string body
        rex = re.compile("(фыва)".encode("cp1251"))
        self.assertEqual("фыва".encode("cp1251"), self.doc.rex_search(rex).group(1))

    def test_rex3(self) -> None:
        # # Search for non-unicode rex in unicode body should fail
        pattern = "(фыва)".encode("utf-8")
        rex = re.compile(pattern)
        self.assertRaises(DataNotFound, lambda: self.doc.rex_search(rex))

    def test_rex4(self) -> None:
        # # Search for unicode rex in byte-string body should fail
        # updated: whatever it has mean 10 years ago,
        # it works in new grab which ignores byte argument
        rex = re.compile("фыва", re.U)
        self.assertEqual("фыва", self.doc.rex_search(rex).group(0))

    def test_rex5(self) -> None:
        # # Search for unexesting fragment
        rex = re.compile("(фыва2)", re.U)
        self.assertRaises(DataNotFound, lambda: self.doc.rex_search(rex))

    def test_assert_rex(self) -> None:
        self.doc.rex_assert(re.compile("фыва"))
        self.doc.rex_assert(re.compile("фыва".encode("cp1251")))

    def test_assert_rex_text(self) -> None:
        self.assertEqual("ха", self.doc.rex_text('<em id="fly-em">([^<]+)'))
