from test.util import BaseGrabTestCase
from test.util import build_grab


class ExtensionPyqueryTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_pyquery_handler(self):
        self.server.response['get.data'] =\
            '<body><h1>Hello world</h1><footer>2014</footer>'
        g = build_grab()
        g.go(self.server.get_url())

        self.assertEqual(g.doc.pyquery('h1').text(), 'Hello world')
