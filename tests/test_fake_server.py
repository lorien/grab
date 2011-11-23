from unittest import TestCase
import urllib

from util import FakeServerThread, RESPONSE, BASE_URL

class TestFakeServer(TestCase):
    def setUp(self):
        FakeServerThread().start()

    def test_get(self):
        RESPONSE['get'] = 'zorro'
        data = urllib.urlopen(BASE_URL).read()
        self.assertEqual(data, RESPONSE['get'])

    def test_post(self):
        RESPONSE['post'] = 'foo'
        data = urllib.urlopen(BASE_URL, 'THE POST').read()
        self.assertEqual(data, RESPONSE['post'])
