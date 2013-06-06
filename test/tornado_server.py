from unittest import TestCase
import urllib

from .tornado_util import SERVER

class TestTornadoServer(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_get(self):
        SERVER.RESPONSE['get'] = 'zorro'
        data = urllib.urlopen(SERVER.BASE_URL).read()
        self.assertEqual(data, SERVER.RESPONSE['get'])

    def test_path(self):
        urllib.urlopen(SERVER.BASE_URL + '/foo').read()
        self.assertEqual(SERVER.REQUEST['path'], '/foo')

        urllib.urlopen(SERVER.BASE_URL + '/foo?bar=1').read()
        self.assertEqual(SERVER.REQUEST['path'], '/foo')
        self.assertEqual(SERVER.REQUEST['args']['bar'], '1')


    def test_post(self):
        SERVER.RESPONSE['post'] = 'foo'
        data = urllib.urlopen(SERVER.BASE_URL, 'THE POST').read()
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
        urllib.urlopen(SERVER.BASE_URL).read()
        self.assertEqual(gen.count, 1)
        urllib.urlopen(SERVER.BASE_URL).read()
        self.assertEqual(gen.count, 2)
        # Now create POST request which should no be
        # processed with ContentGenerator which is bind to GET
        # requests
        urllib.urlopen(SERVER.BASE_URL, 'some post').read()
        self.assertEqual(gen.count, 2)
