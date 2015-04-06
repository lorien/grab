# coding: utf-8
from grab import GrabMisuseError, GrabError
from grab.error import GrabTooManyRedirectsError
from grab.base import reset_request_counter
from test.util import build_grab
from test.util import BaseGrabTestCase
import six
import tempfile
import os


class GrabApiTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_incorrect_option_name(self):
        g = build_grab()
        self.assertRaises(GrabMisuseError, g.setup,
                          save_the_word=True)

    # Ghost test was disabled because of strange error
    # that appear when multiple Ghost instances are created
    def test_clone(self):
        g = build_grab()
        self.server.response['get.data'] = 'Moon'
        g.go(self.server.get_url())
        self.assertTrue(b'Moon' in g.response.body)
        self.server.response['post.data'] = 'Foo'
        g2 = g.clone(method='post')
        g2.go(self.server.get_url())
        self.assertTrue(b'Foo' in g2.response.body)

    def test_empty_clone(self):
        g = build_grab()
        g.clone()

    def test_adopt(self):
        g = build_grab()
        self.server.response['get.data'] = 'Moon'
        g.go(self.server.get_url())
        g2 = build_grab()
        self.assertEqual(g2.config['url'], None)
        g2.adopt(g)
        self.assertTrue(b'Moon' in g2.response.body)
        self.assertEqual(g2.config['url'], self.server.get_url())

    def test_empty_adopt(self):
        g = build_grab()
        g2 = build_grab()
        g2.adopt(g)

    def test_default_content_for_fake_response(self):
        content = b'<strong>test</strong>'
        g = build_grab(document_body=content)
        self.assertEqual(g.response.body, content)

    def test_inheritance(self):
        from grab import Grab

        class SimpleExtension(object):
            data = {'counter': 0}

            @classmethod
            def get_data(cls):
                return cls.data

        class CustomGrab(Grab, SimpleExtension):
            pass

        SimpleExtension.get_data()['counter'] = 0
        CustomGrab()
        # self.assertEqual(SimpleExtension.get_data()['counter'], 1)

        class VeryCustomGrab(CustomGrab):
            pass

        SimpleExtension.get_data()['counter'] = 0
        VeryCustomGrab()
        # self.assertEqual(SimpleExtension.get_data()['counter'], 1)

    def test_request_counter(self):
        import threading

        reset_request_counter()
        g = build_grab()
        g.go(self.server.get_url())
        self.assertEqual(g.request_counter, 1)

        g.go(self.server.get_url())
        self.assertEqual(g.request_counter, 2)

        def func():
            g = build_grab()
            g.go(self.server.get_url())

        # Make 10 requests in concurrent threads
        threads = []
        for x in six.moves.range(10):
            th = threading.Thread(target=func)
            threads.append(th)
            th.start()
        for th in threads:
            th.join()

        g.go(self.server.get_url())
        self.assertEqual(g.request_counter, 13)

    def test_download(self):
        fd, path = tempfile.mkstemp()
        g = build_grab()
        self.server.response['get.data'] = 'FOO'
        length = g.download(self.server.get_url(), path)
        self.assertEqual(3, length)
        os.unlink(path)

    def test_follow_refresh_option(self):
        def handler():
            response = "<meta http-equiv='refresh' content='0;url= %s'>" % \
                       self.server.get_url()
            yield response.encode('ascii')
            yield response.encode('ascii')
            yield response.encode('ascii')
            yield b'OK'

        self.server.response['data'] = handler()
        g = build_grab(follow_refresh=True)
        g.go(self.server.get_url())
        self.assertEqual(g.response.body, b'OK')
        self.server.response['data'] = handler()
        g.setup(redirect_limit=1)
        self.assertRaises(GrabTooManyRedirectsError, g.go,
                          self.server.get_url())

    def test_make_url_absolute(self):
        g = build_grab()
        self.server.response['get.data'] = '<base href="http://foo/bar/">'
        g.go(self.server.get_url())
        absolute_url = g.make_url_absolute('/foobar', resolve_base=True)
        self.assertEqual(absolute_url, 'http://foo/foobar')
        g = build_grab()
        absolute_url = g.make_url_absolute('/foobar')
        self.assertEqual(absolute_url, '/foobar')

    def test_error_request(self):
        g = build_grab()
        g.setup(post={'foo': 'bar'})

        self.assertRaises(GrabError, g.go,
                          url='Could not resolve host address')
        self.assertEqual(g.config['post'], None)
        self.assertEqual(g.config['multipart_post'], None)
        self.assertEqual(g.config['method'], None)
        self.assertEqual(g.config['body_storage_filename'], None)
        self.assertEqual(g.config['refresh_redirect_count'], 0)

    def test_setup_document(self):
        data = b'''
        <h1>test</h1>
        '''
        g = build_grab(data)
        self.assertTrue(b'test' in g.doc.body)

    def test_setup_document_invalid_input(self):
        data = u'''
        <h1>test</h1>
        '''
        self.assertRaises(GrabMisuseError, build_grab, data)
