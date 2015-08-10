# coding: utf-8
from test.util import build_grab
from test.util import BaseGrabTestCase

from grab.error import GrabInternalError, GrabCouldNotResolveHostError


class GrabRequestTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_get_method(self):
        g = build_grab()
        g.go(self.server.get_url())
        self.assertEquals('GET', self.server.request['method'])

    def test_delete_method(self):
        g = build_grab()
        g.setup(method='delete')
        g.go(self.server.get_url())
        self.assertEquals('DELETE', self.server.request['method'])

    def test_put_method(self):
        g = build_grab()
        g.setup(method='put', post=b'abc')
        g.go(self.server.get_url())
        self.assertEquals('PUT', self.server.request['method'])
        self.assertEquals('3', self.server.request['headers']['Content-Length'])

    def test_head_with_invalid_bytes(self):
        def callback(server):
            server.set_status(200)
            server.add_header('Hello-Bug', b'start\xa0end')
            server.write('')
            server.finish()

        self.server.response['callback'] = callback
        g = build_grab()
        g.go(self.server.get_url())

    def test_redirect_with_invalid_byte(self):
        url = self.server.get_url()
        invalid_url = b'http://\xa0' + url.encode('ascii')

        def callback(server):
            server.set_status(301)
            server.add_header('Location', invalid_url)
            server.write('')
            server.finish()

        self.server.response['callback'] = callback
        g = build_grab()
        self.assertRaises((GrabInternalError, GrabCouldNotResolveHostError),
                          g.go, self.server.get_url())
