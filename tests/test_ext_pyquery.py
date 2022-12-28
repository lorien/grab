from test_server import Response

from grab import request
from tests.util import BaseTestCase


class ExtensionPyqueryTestCase(BaseTestCase):
    backend = "pyquery"

    def setUp(self) -> None:
        self.server.reset()

    def test_pyquery_handler(self) -> None:
        self.server.add_response(
            Response(data=b"<body><h1>Hello world</h1><footer>2014</footer>")
        )
        doc = request(self.server.get_url())

        self.assertEqual(doc.pyquery("h1").text(), "Hello world")

    def test_national_utf_symbol(self) -> None:
        msg = (
            "P.S. Bir daha öz fikrimi xatırladım ki,rhen ve "
            "qelben sene bağlı insan başqasına ehtiyac duymaz."
        )
        self.server.add_response(
            Response(data=b"<html><body><p>%s</p></body>" % msg.encode("utf-8"))
        )
        doc = request(self.server.get_url())
        self.assertEqual(doc.pyquery("p")[0].text_content(), msg)
