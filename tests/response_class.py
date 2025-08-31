# coding: utf-8
from __future__ import absolute_import
import os.path

from tests.util import TEST_DIR, build_grab, temp_dir
from tests.util import BaseGrabTestCase

HTML = """
Hello world
"""

IMG_FILE = os.path.join(TEST_DIR, 'files', 'yandex.png')


class TestResponse(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_save(self):
        "Test `Response.save` method."
        with temp_dir() as tmp_dir:
            with open(IMG_FILE, 'rb') as inp:
                img_data = inp.read()
            tmp_file = os.path.join(tmp_dir, 'file.bin')
            self.server.response['get.data'] = img_data

            grab = build_grab()
            grab.go(self.server.get_url())
            grab.doc.save(tmp_file)
            with open(tmp_file, 'rb') as inp:
                self.assertEqual(inp.read(), img_data)

    def test_save_hash(self):
        "Test `Response.save_hash` method."
        with temp_dir() as tmp_dir:
            with open(IMG_FILE, 'rb') as inp:
                img_data = inp.read()
            self.server.response['get.data'] = img_data

            grab = build_grab()
            grab.go(self.server.get_url())
            path = grab.doc.save_hash(self.server.get_url(), tmp_dir)
            with open(os.path.join(tmp_dir, path), 'rb') as inp:
                test_data = inp.read()
            self.assertEqual(test_data, img_data)

    def test_custom_charset(self):
        self.server.response['get.data'] = u'<html><head><meta '\
            u'http-equiv="Content-Type" content="text/html; '\
            u'charset=utf8;charset=cp1251" /></head><body>'\
            u'<h1>крокодил</h1></body></html>'.encode('utf-8')
        grab = build_grab()
        grab.setup(document_charset='utf-8')
        grab.go(self.server.get_url())
        self.assertTrue(u'крокодил' in grab.doc.unicode_body())

    def test_xml_declaration(self):
        """
        unicode_body() should return HTML with xml declaration (if it
        exists in original HTML)
        """
        self.server.response['get.data'] = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<html><body><h1>тест</h1></body></html>'
        )
        grab = build_grab()
        grab.go(self.server.get_url())
        ubody = grab.doc.unicode_body()
        self.assertTrue(u'тест' in ubody)
        self.assertTrue('<?xml' in ubody)
