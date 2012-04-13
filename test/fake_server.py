from unittest import TestCase
import urllib

from util import FakeServerThread, RESPONSE, BASE_URL, REQUEST

class TestFakeServer(TestCase):
    def setUp(self):
        FakeServerThread().start()

    def test_get(self):
        RESPONSE['get'] = 'zorro'
        data = urllib.urlopen(BASE_URL).read()
        self.assertEqual(data, RESPONSE['get'])

    def test_path(self):
        urllib.urlopen(BASE_URL + '/foo').read()
        self.assertEqual(REQUEST['path'], '/foo')

        urllib.urlopen(BASE_URL + '/foo?bar=1').read()
        self.assertEqual(REQUEST['path'], '/foo?bar=1')


    def test_post(self):
        RESPONSE['post'] = 'foo'
        data = urllib.urlopen(BASE_URL, 'THE POST').read()
        self.assertEqual(data, RESPONSE['post'])
