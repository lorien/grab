# coding: utf-8
from unittest import TestCase

from grab.util.py3k_support import *
from grab import GrabMisuseError
from test.util import ignore_transport, only_transport, build_grab
from test.server import SERVER

#from grab.util.py3k_support import *

class GrabApiTestCase(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_incorrect_option_name(self):
        g = build_grab()
        self.assertRaises(GrabMisuseError,
            lambda: g.setup(save_the_word=True))

    @ignore_transport('ghost.GhostTransport')
    # Ghost test was disabled because of strange error
    # that appear when multiple Ghost instances are created
    def test_clone(self):
        g = build_grab()
        SERVER.RESPONSE['get'] = 'Moon'
        g.go(SERVER.BASE_URL)
        self.assertTrue(b'Moon' in g.response.body)
        g2 = build_grab()
        #self.assertEqual(g2.doc.grab, g2)
        g2 = g.clone()
        self.assertTrue(b'Moon' in g.response.body)

    @ignore_transport('ghost.GhostTransport')
    def test_empty_clone(self):
        g = build_grab()
        g.clone()

    @ignore_transport('ghost.GhostTransport')
    def test_adopt(self):
        g = build_grab()
        SERVER.RESPONSE['get'] = 'Moon'
        g.go(SERVER.BASE_URL)
        g2 = build_grab()
        self.assertEqual(g2.config['url'], None)
        g2.adopt(g)
        self.assertTrue(b'Moon' in g2.response.body)
        self.assertEqual(g2.config['url'], SERVER.BASE_URL)

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

            #def extra_init(self):
                #self.get_data()['counter'] += 1

            @classmethod
            def get_data(cls):
                return cls.data

        class CustomGrab(Grab, SimpleExtension):
            pass

        SimpleExtension.get_data()['counter'] = 0
        g = CustomGrab()
        #self.assertEqual(SimpleExtension.get_data()['counter'], 1)

        class VeryCustomGrab(CustomGrab):
            pass

        SimpleExtension.get_data()['counter'] = 0
        g = VeryCustomGrab()
        #self.assertEqual(SimpleExtension.get_data()['counter'], 1)


        # TODO: what did I mean? :)
        # Anyway it does not work now :)
        #class VeryCustomGrab(CustomGrab, SimpleExtension):
            #pass

        #SimpleExtension.get_data()['counter'] = 0
        #g = VeryCustomGrab()
        #self.assertEqual(SimpleExtension.get_data()['counter'], 2)

    @ignore_transport('grab.transport.kit.KitTransport')
    def test_request_counter(self):
        import grab.base
        import itertools
        import threading

        grab.base.REQUEST_COUNTER = itertools.count(1)
        g = build_grab()
        g.go(SERVER.BASE_URL)
        self.assertEqual(g.request_counter, 1)

        g.go(SERVER.BASE_URL)
        self.assertEqual(g.request_counter, 2)

        def func():
            g = build_grab()
            g.go(SERVER.BASE_URL)

        # Make 10 requests in concurrent threads
        threads = []
        for x in xrange(10):
            th = threading.Thread(target=func)
            threads.append(th)
            th.start()
        for th in threads:
            th.join()

        g.go(SERVER.BASE_URL)
        self.assertEqual(g.request_counter, 13)
