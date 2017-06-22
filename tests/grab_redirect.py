from grab.error import GrabTooManyRedirectsError
from tests.util import BaseGrabTestCase, build_grab


def build_location_callback(url, counter):
    meta = {
        'counter': counter,
        'url': url,
    }

    def callback(server):
        if meta['counter']:
            server.set_status(301)
            server.set_header('Location', meta['url'])
        else:
            server.set_status(200)
            server.write('done')
        server.finish()
        meta['counter'] -= 1
    return callback


def build_refresh_callback(url, counter):
    meta = {
        'counter': counter,
        'url': url,
    }

    def callback(server):
        if meta['counter']:
            server.set_status(200)
            server.write('<html><head><meta '
                         'http-equiv="refresh" content="5"></head>')
        else:
            server.set_status(200)
            server.write('done')
        server.finish()
        meta['counter'] -= 1
    return callback


class GrabRedirectTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_follow_refresh_off(self):
        # By default meta-redirect is off
        meta_url = self.server.get_url('/foo')

        self.server.response_once['get.data'] =\
            '<meta http-equiv="refresh" content="5; url=%s">' % meta_url
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertEqual(self.server.request['path'], '/')
        self.assertEqual(grab.doc.url, self.server.get_url())

    def test_follow_refresh_on(self):
        meta_url = self.server.get_url('/foo')
        # Now test meta-auto-redirect
        self.server.response_once['get.data'] =\
            '<meta http-equiv="refresh" content="5; url=%s">' % meta_url
        grab = build_grab()
        grab.setup(follow_refresh=True)
        grab.go(self.server.get_url())
        self.assertEqual(self.server.request['path'], '/foo')
        self.assertEqual(grab.doc.url, meta_url)

    def test_spaces_in_refresh_url(self):
        meta_url = self.server.get_url('/foo')
        # Test spaces in meta tag
        self.server.response_once['get.data'] =\
            "<meta http-equiv='refresh' content='0;url= %s'>" % meta_url
        grab = build_grab()
        grab.setup(follow_refresh=True)
        grab.go(self.server.get_url())
        self.assertEqual(self.server.request['path'], '/foo')
        self.assertEqual(grab.doc.url, meta_url)

    def test_refresh_redirect_limit(self):
        self.server.response['get.callback'] =\
            build_refresh_callback(self.server.get_url(), 10)

        grab = build_grab()
        grab.setup(redirect_limit=10, follow_refresh=True)
        grab.go(self.server.get_url())
        self.assertTrue(b'done' in grab.doc.body)

        self.server.response['get.callback'] =\
            build_refresh_callback(self.server.get_url(), 10)
        grab.setup(redirect_limit=5, follow_refresh=True)
        self.assertRaises(GrabTooManyRedirectsError,
                          lambda: grab.go(self.server.get_url()))

    def test_redirect_limit(self):
        self.server.response['get.callback'] =\
            build_location_callback(self.server.get_url(), 10)

        grab = build_grab()
        grab.setup(redirect_limit=5)

        self.assertRaises(GrabTooManyRedirectsError,
                          lambda: grab.go(self.server.get_url()))

        self.server.response['get.callback'] =\
            build_location_callback(self.server.get_url(), 10)
        grab.setup(redirect_limit=20)
        grab.go(self.server.get_url())
        self.assertTrue(b'done' in grab.doc.body)
