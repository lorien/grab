from tests.util import BaseGrabTestCase
from tests.util import build_grab


class ExtensionPyqueryTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_pyquery_handler(self):
        self.server.response['get.data'] =\
            '<body><h1>Hello world</h1><footer>2014</footer>'
        grab = build_grab()
        grab.go(self.server.get_url())

        self.assertEqual(grab.doc.pyquery('h1').text(), 'Hello world')
