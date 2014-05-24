from unittest import TestCase

from test.server import SERVER
from test.util import build_grab

class ExtensionPyqueryTestCase(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_pyquery_handler(self):
        SERVER.RESPONSE['get'] = '<body><h1>Hello world</h1><footer>2014</footer>'
        g = build_grab()
        g.go(SERVER.BASE_URL)

        self.assertEqual(g.doc.pyquery('h1').text(), 'Hello world')
