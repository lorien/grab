# coding: utf-8
from unittest import TestCase
import os

from grab import Grab, GrabMisuseError
from test.util import TMP_DIR, ignore_transport, only_transport, build_grab
from test.server import SERVER


class GrabSimpleTestCase(TestCase):
    def setUp(self):
        SERVER.reset()

    @ignore_transport('grab.transport.kit.KitTransport')
    def test_body_inmemory(self):
        g = build_grab()
        g.setup(body_inmemory=False)
        self.assertRaises(GrabMisuseError, lambda: g.go(SERVER.BASE_URL))

        SERVER.RESPONSE['get'] = 'foo'
        g = build_grab()
        g.setup(body_inmemory=False)
        g.setup(body_storage_dir=TMP_DIR)
        g.go(SERVER.BASE_URL)
        #self.assertTrue(os.path.exists(g.response.body_path))
        #self.assertTrue(TMP_DIR in g.response.body_path)
        #self.assertEqual('foo', open(g.response.body_path).read())
        #old_path = g.response.body_path

        #g.go(SERVER.BASE_URL)
        #self.assertTrue(old_path != g.response.body_path)

        #SERVER.RESPONSE['get'] = 'foo'
        #g = build_grab()
        #g.setup(body_inmemory=False)
        #g.setup(body_storage_dir=TMP_DIR)
        #g.setup(body_storage_filename='musik.mp3')
        #g.go(SERVER.BASE_URL)
        #self.assertTrue(os.path.exists(g.response.body_path))
        #self.assertTrue(TMP_DIR in g.response.body_path)
        #self.assertEqual('foo', open(g.response.body_path).read())
        #self.assertEqual(os.path.join(TMP_DIR, 'musik.mp3'), g.response.body_path)
        #self.assertEqual(g.response.body, 'foo')
        #self.assertEqual(g.response._cached_body, None)
