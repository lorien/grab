# coding: utf-8
from grab import GrabMisuseError
from test.util import TMP_DIR, build_grab
from test.util import BaseGrabTestCase
import os


class GrabSimpleTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_body_inmemory_false(self):
        g = build_grab()
        g.setup(body_inmemory=False)
        self.assertRaises(GrabMisuseError, lambda: g.go(self.server.get_url()))

        self.server.response['get.data'] = b'foo'
        g = build_grab()
        g.setup(body_inmemory=False)
        g.setup(body_storage_dir=TMP_DIR)
        g.go(self.server.get_url())
        self.assertTrue(os.path.exists(g.response.body_path))
        self.assertTrue(TMP_DIR in g.response.body_path)
        self.assertEqual(b'foo', open(g.response.body_path, 'rb').read())
        self.assertEqual(g.response._bytes_body, None)
        old_path = g.response.body_path

        g.go(self.server.get_url())
        self.assertTrue(old_path != g.response.body_path)

        self.server.response['get.data'] = 'foo'
        g = build_grab()
        g.setup(body_inmemory=False)
        g.setup(body_storage_dir=TMP_DIR)
        g.setup(body_storage_filename='music.mp3')
        g.go(self.server.get_url())
        self.assertTrue(os.path.exists(g.response.body_path))
        self.assertTrue(TMP_DIR in g.response.body_path)
        self.assertEqual(b'foo', open(g.response.body_path, 'rb').read())
        self.assertEqual(os.path.join(TMP_DIR, 'music.mp3'),
                         g.response.body_path)
        self.assertEqual(g.response.body, b'foo')
        self.assertEqual(g.response._bytes_body, None)

    def test_body_inmemory_true(self):
        g = build_grab()
        self.server.response['data'] = b'bar'
        g.go(self.server.get_url())
        self.assertEqual(g.response._bytes_body, b'bar')

    def test_assign_unicode_to_body(self):
        g = build_grab()
        g.doc.body = b'abc'
        g.doc.body = b'def'

        def bad_func():
            g.doc.body = u'Спутник' 

        self.assertRaises(GrabMisuseError, bad_func)
