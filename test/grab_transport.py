import pickle

from test.util import BaseGrabTestCase
from grab import Grab
from grab.transport.curl import CurlTransport
from grab.error import GrabMisuseError


class FakeTransport(CurlTransport):
    def prepare_response(self, grab):
        resp = super(FakeTransport, self).prepare_response(grab)
        resp.body = b'Faked ' + resp.body
        return resp


def get_curl_transport():
    return CurlTransport()


def get_fake_transport():
    return FakeTransport()


class TestTransportTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()
        self.server.response['get.data'] = 'XYZ'

    def transport_option_logic(self, curl_transport, fake_transport):
        grab = Grab(transport=curl_transport)
        grab.go(self.server.get_url())
        self.assertEqual(grab.response.body, b'XYZ')

        grab2 = grab.clone()
        grab.go(self.server.get_url())
        self.assertEqual(grab.response.body, b'XYZ')

        grab2_data = pickle.dumps(grab2, pickle.HIGHEST_PROTOCOL)
        grab3 = pickle.loads(grab2_data)
        grab3.go(self.server.get_url())
        self.assertEqual(grab3.response.body, b'XYZ')

        grab = Grab(transport=fake_transport)
        grab.go(self.server.get_url())
        self.assertEqual(grab.response.body, b'Faked XYZ')

        grab2 = grab.clone()
        grab.go(self.server.get_url())
        self.assertEqual(grab.response.body, b'Faked XYZ')

        grab2_data = pickle.dumps(grab2, pickle.HIGHEST_PROTOCOL)
        grab3 = pickle.loads(grab2_data)
        grab3.go(self.server.get_url())
        self.assertEqual(grab3.response.body, b'Faked XYZ')

    def test_transport_option_as_string(self):
        self.transport_option_logic(
            'grab.transport.curl.CurlTransport',
            'test.grab_transport.FakeTransport',
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

    def test_invalid_transport_nodot(self):
        def func():
            Grab(transport='zzzzzzzzzz')
        self.assertRaises(GrabMisuseError, func)

    def test_invalid_transport_not_collable_or_string(self):
        def func():
            Grab(transport=4)
        self.assertRaises(GrabMisuseError, func)
