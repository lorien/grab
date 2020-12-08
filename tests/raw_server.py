from unittest import TestCase
from urllib.request import urlopen

from .util import start_raw_server, stop_raw_server


class RawServerTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw_server = start_raw_server()

    @classmethod
    def tearDownClass(cls):
        stop_raw_server(cls.raw_server)

    def test_response(self):
        self.raw_server.response['data'] = (
            b'HTTP/1.1 200 OK\r\n\r\n'
            b'FOO'
        )
        res = urlopen(self.raw_server.get_url())
        self.assertEqual(res.read(), b'FOO')

    def test_sequential_responses(self):
        self.raw_server.response['data'] = (
            b'HTTP/1.1 200 OK\r\n\r\n'
            b'FOO'
        )
        res = urlopen(self.raw_server.get_url())
        self.assertEqual(res.read(), b'FOO')

        self.raw_server.response['data'] = (
            b'HTTP/1.1 200 OK\r\n\r\n'
            b'BAR'
        )
        res = urlopen(self.raw_server.get_url())
        self.assertEqual(res.read(), b'BAR')
