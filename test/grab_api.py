# coding: utf-8
from grab.util.py3k_support import *  # noqa
from grab import GrabMisuseError
from grab.base import reset_request_counter
from test.util import build_grab
from test.util import BaseGrabTestCase


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
        g2 = g.clone()
        self.assertTrue(b'Moon' in g2.response.body)

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
        content = '<strong>test</strong>'
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
        for x in xrange(10):
            th = threading.Thread(target=func)
            threads.append(th)
            th.start()
        for th in threads:
            th.join()

        g.go(self.server.get_url())
        self.assertEqual(g.request_counter, 13)
