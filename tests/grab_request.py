# coding: utf-8
from tests.util import build_grab, exclude_grab_transport
from tests.util import BaseGrabTestCase

from grab.error import (GrabInternalError, GrabCouldNotResolveHostError,
                        GrabTimeoutError)


class GrabRequestTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_get_method(self):
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertEqual('GET', self.server.request['method'])

    def test_delete_method(self):
        grab = build_grab()
        grab.setup(method='delete')
        grab.go(self.server.get_url())
        self.assertEqual('DELETE', self.server.request['method'])

    def test_put_method(self):
        grab = build_grab()
        grab.setup(method='put', post=b'abc')
        grab.go(self.server.get_url())
        self.assertEqual('PUT', self.server.request['method'])
        self.assertEqual('3', self.server.request['headers']['Content-Length'])

    def test_head_with_invalid_bytes(self):
        def callback(server):
            server.set_status(200)
            server.add_header('Hello-Bug', b'start\xa0end')
            server.write('')
            server.finish()

        self.server.response['callback'] = callback
        grab = build_grab()
        grab.go(self.server.get_url())

    @exclude_grab_transport('urllib3')
    def test_redirect_with_invalid_byte(self):
        url = self.server.get_url()
        invalid_url = b'http://\xa0' + url.encode('ascii')

        def callback(server):
            server.set_status(301)
            server.add_header('Location', invalid_url)
            server.write('')
            server.finish()

        self.server.response['callback'] = callback
        grab = build_grab()
        # GrabTimeoutError raised when tests are being runned on computer
        # without access to the internet (no DNS service available)
        self.assertRaises((GrabInternalError, GrabCouldNotResolveHostError,
                           GrabTimeoutError),
                          grab.go, self.server.get_url())

    def test_options_method(self):
        grab = build_grab()
        grab.setup(method='options', post=b'abc')
        grab.go(self.server.get_url())
        self.assertEqual('OPTIONS', self.server.request['method'])
        self.assertEqual('3', self.server.request['headers']['Content-Length'])

        grab = build_grab()
        grab.setup(method='options')
        grab.go(self.server.get_url())
        self.assertEqual('OPTIONS', self.server.request['method'])
        self.assertTrue('Content-Length' not in self.server.request['headers'])

    @exclude_grab_transport('urllib3')
    def test_request_headers(self):
        grab = build_grab(debug=True)
        grab.setup(headers={'Foo': 'Bar'})
        grab.go(self.server.get_url())
        self.assertEqual('Bar', grab.request_headers['foo'])
