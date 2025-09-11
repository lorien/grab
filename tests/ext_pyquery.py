# coding: utf-8
from test_server import Response
from tests.util import BaseGrabTestCase, build_grab


class ExtensionPyqueryTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_pyquery_handler(self):
        self.server.add_response(
            Response(data="<body><h1>Hello world</h1><footer>2014</footer>")
        )
        grab = build_grab()
        grab.go(self.server.get_url())

        self.assertEqual(grab.doc.pyquery("h1").text(), "Hello world")

    def test_national_utf_symbol(self):
        # fmt: off
        msg = (
            u"P.S. Bir daha öz fikrimi xatırladım ki,rhen ve "
            u"qelben sene bağlı insan başqasına ehtiyac duymaz."
        )
        data = u"<html><body><p>{}</p></body></html".format(msg).encode("utf-8")
        # fmt: on
        self.server.add_response(Response(data=data))
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertEqual(grab.doc.pyquery("p")[0].text_content(), msg)
