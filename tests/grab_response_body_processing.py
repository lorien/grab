# coding: utf-8
import os

from tests.util import temp_dir, build_grab, TEST_DIR
from tests.util import BaseGrabTestCase

from grab import GrabMisuseError


class GrabSimpleTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_body_inmemory_false(self):
        with temp_dir() as tmp_dir:
            grab = build_grab()
            grab.setup(body_inmemory=False)
            with self.assertRaises(GrabMisuseError):
                grab.go(self.server.get_url())

            self.server.response['get.data'] = b'foo'
            grab = build_grab()
            grab.setup(body_inmemory=False)
            grab.setup(body_storage_dir=tmp_dir)
            grab.go(self.server.get_url())
            self.assertTrue(os.path.exists(grab.doc.body_path))
            self.assertTrue(tmp_dir in grab.doc.body_path)
            with open(grab.doc.body_path, 'rb') as inp:
                self.assertEqual(b'foo', inp.read())
            # pylint: disable=protected-access
            self.assertEqual(grab.doc._bytes_body, None)
            # pylint: enable=protected-access
            old_path = grab.doc.body_path

            grab.go(self.server.get_url())
            self.assertTrue(old_path != grab.doc.body_path)

        with temp_dir() as tmp_dir:
            self.server.response['get.data'] = 'foo'
            grab = build_grab()
            grab.setup(body_inmemory=False)
            grab.setup(body_storage_dir=tmp_dir)
            grab.setup(body_storage_filename='music.mp3')
            grab.go(self.server.get_url())
            self.assertTrue(os.path.exists(grab.doc.body_path))
            self.assertTrue(tmp_dir in grab.doc.body_path)
            with open(grab.doc.body_path, 'rb') as inp:
                self.assertEqual(b'foo', inp.read())
            self.assertEqual(os.path.join(tmp_dir, 'music.mp3'),
                             grab.doc.body_path)
            self.assertEqual(grab.doc.body, b'foo')
            # pylint: disable=protected-access
            self.assertEqual(grab.doc._bytes_body, None)
            # pylint: enable=protected-access

    def test_body_inmemory_true(self):
        grab = build_grab()
        self.server.response['data'] = b'bar'
        grab.go(self.server.get_url())
        # pylint: disable=protected-access
        self.assertEqual(grab.doc._bytes_body, b'bar')
        # pylint: enable=protected-access

    def test_assign_unicode_to_body(self):
        grab = build_grab()
        grab.doc.body = b'abc'
        grab.doc.body = b'def'

        with self.assertRaises(GrabMisuseError):
            grab.doc.body = u'Спутник'

    def test_empty_response(self):
        self.server.response['data'] = b''
        grab = build_grab()
        grab.go(self.server.get_url())
        # pylint: disable=pointless-statement
        grab.doc.tree # should not raise exception
        # pylint: enable=pointless-statement

    def test_doc_tree_notags_document(self):
        data = b'test'
        grab = build_grab(data)
        self.assertEqual(grab.doc('//html').text(), 'test')

    def test_github_html_processing(self):
        """This test is for osx and py3.5
        See: https://github.com/lorien/grab/issues/199"""
        path = os.path.join(TEST_DIR, 'files/github_showcases.html')
        grab = build_grab()
        if '\\' in path:
            path = path.replace('\\', '/')
        grab.go('file://' + path)
        for elem in grab.doc('//a[contains(@class, "exploregrid-item")]'):
            print(grab.make_url_absolute(elem.attr('href')))
