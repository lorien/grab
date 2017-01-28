# coding: utf-8
from grab import GrabMisuseError
from test.util import temp_dir, build_grab
from test.util import BaseGrabTestCase
import os


class GrabSimpleTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_body_inmemory_false(self):
        with temp_dir() as tmp_dir:
            g = build_grab()
            g.setup(body_inmemory=False)
            self.assertRaises(GrabMisuseError, lambda: g.go(self.server.get_url()))

            self.server.response['get.data'] = b'foo'
            g = build_grab()
            g.setup(body_inmemory=False)
            g.setup(body_storage_dir=tmp_dir)
            g.go(self.server.get_url())
            self.assertTrue(os.path.exists(g.response.body_path))
            self.assertTrue(tmp_dir in g.response.body_path)
            self.assertEqual(b'foo', open(g.response.body_path, 'rb').read())
            self.assertEqual(g.response._bytes_body, None)
            old_path = g.response.body_path

            g.go(self.server.get_url())
            self.assertTrue(old_path != g.response.body_path)

        with temp_dir() as tmp_dir:
            self.server.response['get.data'] = 'foo'
            g = build_grab()
            g.setup(body_inmemory=False)
            g.setup(body_storage_dir=tmp_dir)
            g.setup(body_storage_filename='music.mp3')
            g.go(self.server.get_url())
            self.assertTrue(os.path.exists(g.response.body_path))
            self.assertTrue(tmp_dir in g.response.body_path)
            self.assertEqual(b'foo', open(g.response.body_path, 'rb').read())
            self.assertEqual(os.path.join(tmp_dir, 'music.mp3'),
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

    def test_empty_response(self):
        self.server.response['data'] = b''
        g = build_grab()
        g.go(self.server.get_url())
        g.doc.tree # should not raise exception

    #def test_emoji_processing(self):
    #    #html = u'''
    #    #<html><body>
    #    #    <span class="a-color-base"> 👍🏻 </span>
    #    #</body></html>
    #    #'''.encode('utf-8')
    #    g = build_grab()
    #    #print('>>',g.doc('//span').text(),'<<')
    #    #import grab
    #    #g = grab.Grab()
    #    #g.go('https://github.com/lorien/grab/issues/199#issuecomment-269854859')
    #    g.go('https://en.wikipedia.org/wiki/Emoji')
    #    g.doc.select("//*")

    def test_doc_tree_notags_document(self):
        data = b'test'
        g = build_grab(data)
        self.assertEqual(g.doc('//html').text(), 'test')
