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
