from unittest import TestCase

from grab import Grab
from grab.error import GrabTooManyRedirectsError
from test.server import SERVER
from test.util import GRAB_TRANSPORT, only_transport

class RedirectController(object):
    def __init__(self, counter):
        self.setup_counter(counter)

    def setup_counter(self, counter):
        self.counter = counter

    def request_handler(self, server):
        if self.counter:
            server.set_status(301)
            server.set_header('Location', SERVER.BASE_URL)
        else:
            server.set_status(200)
        self.counter -= 1


class RefreshRedirectController(RedirectController):
    def request_handler(self, server):
        server.set_status(200)
        if self.counter:
            server.write('<html><head><meta http-equiv="refresh" content="5"></head>')
        else:
            server.write('OK')
        self.counter -= 1


class GrabRedirectTestCase(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_meta_refresh_redirect(self):
        # By default meta-redirect is off
        meta_url = SERVER.BASE_URL + '/foo'

        SERVER.RESPONSE_ONCE['get'] = '<meta http-equiv="refresh" content="5; url=%s">' % meta_url
        g = Grab(transport=GRAB_TRANSPORT)
        g.go(SERVER.BASE_URL + '/')
        self.assertEqual(SERVER.REQUEST['path'], '/')
        self.assertEqual(g.response.url, SERVER.BASE_URL + '/')

        # Now test meta-auto-redirect
        SERVER.RESPONSE_ONCE['get'] = '<meta http-equiv="refresh" content="5; url=%s">' % meta_url
        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(follow_refresh=True)
        g.go(SERVER.BASE_URL)
        self.assertEqual(SERVER.REQUEST['path'], '/foo')
        self.assertEqual(g.response.url, meta_url)

        # Test spaces in meta tag
        SERVER.RESPONSE_ONCE['get'] = "<meta http-equiv='refresh' content='0;url= %s'>" % meta_url
        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(follow_refresh=True)
        g.go(SERVER.BASE_URL)
        self.assertEqual(SERVER.REQUEST['path'], '/foo')
        self.assertEqual(g.response.url, meta_url)

    @only_transport('grab.transport.curl.CurlTransport')
    def test_redirect_limit(self):
        ctl = RedirectController(10)
        SERVER.RESPONSE['get_callback'] = ctl.request_handler

        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(redirect_limit=5)

        self.assertRaises(GrabTooManyRedirectsError,
                          lambda: g.go(SERVER.BASE_URL))

        ctl.setup_counter(10)
        g.setup(redirect_limit=20)
        g.go(SERVER.BASE_URL)

    @only_transport('grab.transport.curl.CurlTransport')
    def test_refresh_redirect_limit(self):
        ctl = RefreshRedirectController(10)
        SERVER.RESPONSE['get_callback'] = ctl.request_handler

        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(redirect_limit=5, follow_refresh=False)
        g.go(SERVER.BASE_URL)

        ctl.setup_counter(10)
        g.setup(redirect_limit=5, follow_refresh=True)
        self.assertRaises(GrabTooManyRedirectsError,
                          lambda: g.go(SERVER.BASE_URL))
