# coding: utf-8
from grab import GrabMisuseError
from test.util import TMP_DIR, build_grab
from test.util import BaseGrabTestCase


class GrabSimpleTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_body_inmemory(self):
        g = build_grab()
        g.setup(body_inmemory=False)
        self.assertRaises(GrabMisuseError, lambda: g.go(self.server.get_url()))

        self.server.response['get.data'] = 'foo'
        g = build_grab()
        g.setup(body_inmemory=False)
        g.setup(body_storage_dir=TMP_DIR)
        g.go(self.server.get_url())
        # self.assertTrue(os.path.exists(g.response.body_path))
        # self.assertTrue(TMP_DIR in g.response.body_path)
        # self.assertEqual('foo', open(g.response.body_path).read())
        # old_path = g.response.body_path

        # g.go(self.server.get_url())
        # self.assertTrue(old_path != g.response.body_path)

        # self.server.response['get.data'] = 'foo'
        # g = build_grab()
        # g.setup(body_inmemory=False)
        # g.setup(body_storage_dir=TMP_DIR)
        # g.setup(body_storage_filename='musik.mp3')
        # g.go(self.server.get_url())
        # self.assertTrue(os.path.exists(g.response.body_path))
        # self.assertTrue(TMP_DIR in g.response.body_path)
        # self.assertEqual('foo', open(g.response.body_path).read())
        # self.assertEqual(os.path.join(TMP_DIR, 'musik.mp3'),
        #                  g.response.body_path)
        # self.assertEqual(g.response.body, 'foo')
        # self.assertEqual(g.response._cached_body, None)
