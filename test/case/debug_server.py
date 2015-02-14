from unittest import TestCase
try:
    from urllib import urlopen
except ImportError:
    from urllib.request import urlopen

from test.server import SERVER

class TestTornadoServer(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_get(self):
        SERVER.RESPONSE['get'] = b'zorro'
        data = urlopen(SERVER.BASE_URL).read()
        self.assertEqual(data, SERVER.RESPONSE['get'])

    def test_path(self):
        urlopen(SERVER.BASE_URL + '/foo').read()
        self.assertEqual(SERVER.REQUEST['path'], '/foo')

        urlopen(SERVER.BASE_URL + '/foo?bar=1').read()
        self.assertEqual(SERVER.REQUEST['path'], '/foo')
        self.assertEqual(SERVER.REQUEST['args']['bar'], '1')


    def test_post(self):
        SERVER.RESPONSE['post'] = b'foo'
        data = urlopen(SERVER.BASE_URL, b'THE POST').read()
        self.assertEqual(data, SERVER.RESPONSE['post'])

    def test_callback(self):
        class ContentGenerator():
            def __init__(self):
                self.count = 0

            def __call__(self):
                self.count += 1
                return 'foo'

        gen = ContentGenerator()
        SERVER.RESPONSE['get'] = gen 
        urlopen(SERVER.BASE_URL).read()
        self.assertEqual(gen.count, 1)
        urlopen(SERVER.BASE_URL).read()
        self.assertEqual(gen.count, 2)
        # Now create POST request which should no be
        # processed with ContentGenerator which is bind to GET
        # requests
        urlopen(SERVER.BASE_URL, b'some post').read()
        self.assertEqual(gen.count, 2)
