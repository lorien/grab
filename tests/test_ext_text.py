from grab import DataNotFound
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


class TextExtensionTest(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

        # Create fake grab instance with fake response
        self.doc = Document(HTML, encoding="cp1251")

    def test_search(self) -> None:
        self.assertTrue(self.doc.text_search("фыва".encode("cp1251")))
        self.assertTrue(self.doc.text_search("фыва"))
        self.assertFalse(self.doc.text_search("фыва2"))

    def test_assert_substring(self) -> None:
        self.doc.text_assert("фыва")
        self.doc.text_assert("фыва".encode("cp1251"))
        self.assertRaises(DataNotFound, self.doc.text_assert, "фыва2")

    def test_assert_substrings(self) -> None:
        self.doc.text_assert_any(("фыва",))
        self.doc.text_assert_any(("фывы нет", "фыва"))
        self.doc.text_assert_any(("фыва".encode("cp1251"), "где ты фыва?"))
        self.assertRaises(
            DataNotFound, self.doc.text_assert_any, ("фыва, вернись", "фыва-а-а-а")
        )
