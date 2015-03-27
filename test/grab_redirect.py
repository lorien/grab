from grab import Grab
from grab.error import GrabTooManyRedirectsError
from test.util import BaseGrabTestCase
from test.util import GRAB_TRANSPORT


class RedirectController(object):
    def __init__(self, counter):
        self.setup_counter(counter)

    def setup_counter(self, counter):
        self.counter = counter

    def request_handler(self, server):
        if self.counter:
            server.set_status(301)
            server.set_header('Location', self.server.get_url())
        else:
            server.set_status(200)
        self.counter -= 1


class RefreshRedirectController(RedirectController):
    def request_handler(self, server):
        server.set_status(200)
        if self.counter:
            server.write('<html><head><meta '
                         'http-equiv="refresh" content="5"></head>')
        else:
            server.write('OK')
        self.counter -= 1


class GrabRedirectTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_meta_refresh_redirect(self):
        # By default meta-redirect is off
        meta_url = self.server.get_url() + '/foo'

        self.server.response_once['get.data'] =\
            '<meta http-equiv="refresh" content="5; url=%s">' % meta_url
        g = Grab(transport=GRAB_TRANSPORT)
        g.go(self.server.get_url() + '/')
        self.assertEqual(self.server.request['path'], '/')
        self.assertEqual(g.response.url, self.server.get_url() + '/')

        # Now test meta-auto-redirect
        self.server.response_once['get.data'] =\
            '<meta http-equiv="refresh" content="5; url=%s">' % meta_url
        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(follow_refresh=True)
        g.go(self.server.get_url())
        self.assertEqual(self.server.request['path'], '/foo')
        self.assertEqual(g.response.url, meta_url)

        # Test spaces in meta tag
        self.server.response_once['get.data'] =\
            "<meta http-equiv='refresh' content='0;url= %s'>" % meta_url
        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(follow_refresh=True)
        g.go(self.server.get_url())
        self.assertEqual(self.server.request['path'], '/foo')
        self.assertEqual(g.response.url, meta_url)

    def test_redirect_limit(self):
        ctl = RedirectController(10)
        self.server.response['get_callback'] = ctl.request_handler

        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(redirect_limit=5)

        self.assertRaises(GrabTooManyRedirectsError,
                          lambda: g.go(self.server.get_url()))

        ctl.setup_counter(10)
        g.setup(redirect_limit=20)
        g.go(self.server.get_url())

    def test_refresh_redirect_limit(self):
        ctl = RefreshRedirectController(10)
        self.server.response['get_callback'] = ctl.request_handler

        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(redirect_limit=5, follow_refresh=False)
        g.go(self.server.get_url())

        ctl.setup_counter(10)
        g.setup(redirect_limit=5, follow_refresh=True)
        self.assertRaises(GrabTooManyRedirectsError,
                          lambda: g.go(self.server.get_url()))
