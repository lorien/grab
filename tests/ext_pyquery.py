# coding: utf-8
from tests.util import BaseGrabTestCase
from tests.util import build_grab


class ExtensionPyqueryTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_pyquery_handler(self):
        self.server.response['get.data'] = (
            '<body><h1>Hello world</h1><footer>2014</footer>'
        )
        grab = build_grab()
        grab.go(self.server.get_url())

        self.assertEqual(grab.doc.pyquery('h1').text(), 'Hello world')

    def test_national_utf_symbol(self):
        msg = (
            u'P.S. Bir daha öz fikrimi xatırladım ki,rhen ve '
            u'qelben sene bağlı insan başqasına ehtiyac duymaz.'
        )
        self.server.response['get.data'] = (
            '<html><body><p>%s</p></body>' % msg
        ).encode('utf-8')
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertEqual(grab.doc.pyquery('p')[0].text_content(), msg)
