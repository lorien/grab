import pickle
import os
import sys

from tests.util import BaseGrabTestCase, only_grab_transport, temp_dir
from grab import Grab
from grab.error import GrabMisuseError

FAKE_TRANSPORT_CODE = '''
from grab.transport.curl import CurlTransport

class FakeTransport(CurlTransport):
    pass
'''


def get_fake_transport_class():
    from grab.transport.curl import CurlTransport

    class FakeTransport(CurlTransport):
        pass

    return FakeTransport


def get_fake_transport_instance():
    return get_fake_transport_class()()


def get_curl_transport_instance():
    from grab.transport.curl import CurlTransport

    return CurlTransport()


class TestTransportTestCase(BaseGrabTestCase):
    def assert_transport_response(self, transport, response):
        self.server.response['get.data'] = response

        grab = Grab(transport=transport)
        grab.go(self.server.get_url())
        self.assertEqual(grab.doc.body, response)

        grab2 = grab.clone()
        grab2.go(self.server.get_url())
        self.assertEqual(grab2.doc.body, response)

    def assert_transport_pickle(self, transport, response):
        grab = Grab(transport=transport)
        grab2 = grab.clone()
        grab2_data = pickle.dumps(grab2, pickle.HIGHEST_PROTOCOL)
        grab3 = pickle.loads(grab2_data)
        grab3.go(self.server.get_url())
        self.assertEqual(grab3.doc.body, response)

    @only_grab_transport('pycurl')
    def test_transport_option_as_string_curl(self):
        self.assert_transport_response('grab.transport.curl.CurlTransport',
                                       b'XYZ')

    @only_grab_transport('pycurl')
    def test_transport_option_as_string_fake(self):
        with temp_dir() as dir_:
            sys.path.insert(0, dir_)
            with open(os.path.join(dir_, 'foo.py'), 'w') as out:
                out.write(FAKE_TRANSPORT_CODE)
            self.assert_transport_response('foo.FakeTransport', b'XYZ')
            sys.path.remove(dir_)

    @only_grab_transport('pycurl')
    def test_transport_option_as_class_curl(self):
        from grab.transport.curl import CurlTransport

        self.assert_transport_response(CurlTransport, b'XYZ')

    @only_grab_transport('pycurl')
    def test_transport_option_as_class_fake(self):
        fake_transport_cls = get_fake_transport_class()
        self.assert_transport_response(fake_transport_cls, b'XYZ')

    @only_grab_transport('pycurl')
    def test_transport_option_as_function_curl(self):
        self.assert_transport_response(get_curl_transport_instance, b'XYZ')

    @only_grab_transport('pycurl')
    def test_transport_option_as_function_fake(self):
        self.assert_transport_response(get_fake_transport_instance, b'XYZ')

    def test_invalid_transport_invalid_alias(self):
        with self.assertRaises(GrabMisuseError):
            Grab(transport='zzzzzzzzzz').go(self.server.get_url())

    def test_invalid_transport_invalid_path(self):
        # AttributeError comes from setup_transport method
        with self.assertRaises(AttributeError):
            Grab(
                transport='tests.grab_transport.ZZZ'
            ).go(self.server.get_url())

    def test_invalid_transport_not_collable_or_string(self):
        with self.assertRaises(GrabMisuseError):
            Grab(transport=13).go(self.server.get_url())
