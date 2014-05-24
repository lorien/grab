from unittest import TestCase
import pickle

from grab import Grab
from test.server import SERVER
from grab.transport.curl import CurlTransport

class FakeTransport(CurlTransport):
    def prepare_response(self, grab):
        resp = super(FakeTransport, self).prepare_response(grab)
        resp.body = b'Faked ' + resp.body
        return resp


def get_curl_transport():
    return CurlTransport()


def get_fake_transport():
    return FakeTransport()


class TestTransportTestCase(TestCase):
    def setUp(self):
        SERVER.reset()
        SERVER.RESPONSE['get'] = 'XYZ'

    def transport_option_logic(self, curl_transport, fake_transport):
        g = Grab(transport=curl_transport)
        g.go(SERVER.BASE_URL)
        self.assertEqual(g.response.body, b'XYZ')

        g2 = g.clone()
        g.go(SERVER.BASE_URL)
        self.assertEqual(g.response.body, b'XYZ')

        g2_data = pickle.dumps(g2, pickle.HIGHEST_PROTOCOL)
        g3 = pickle.loads(g2_data)
        g3.go(SERVER.BASE_URL)
        self.assertEqual(g3.response.body, b'XYZ')

        g = Grab(transport=fake_transport)
        g.go(SERVER.BASE_URL)
        self.assertEqual(g.response.body, b'Faked XYZ')

        g2 = g.clone()
        g.go(SERVER.BASE_URL)
        self.assertEqual(g.response.body, b'Faked XYZ')

        g2_data = pickle.dumps(g2, pickle.HIGHEST_PROTOCOL)
        g3 = pickle.loads(g2_data)
        g3.go(SERVER.BASE_URL)
        self.assertEqual(g3.response.body, b'Faked XYZ')

    def test_transport_option_as_string(self):
        self.transport_option_logic(
            'grab.transport.curl.CurlTransport',
            'test.case.grab_transport.FakeTransport',
        )

    def test_transport_option_as_class(self):
        self.transport_option_logic(
            CurlTransport,
            FakeTransport,
        )

    def test_transport_option_as_function(self):
        self.transport_option_logic(
            get_curl_transport,
            get_fake_transport,
        )
