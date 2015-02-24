# coding: utf-8
from __future__ import absolute_import
import os.path

from test.util import TEST_DIR, TMP_DIR, build_grab
from test.util import BaseGrabTestCase

HTML = """
Hello world
"""

IMG_FILE = os.path.join(TEST_DIR, 'files', 'yandex.png')


class TestResponse(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_save(self):
        "Test `Response.save` method."
        img_data = open(IMG_FILE, 'rb').read()
        temp_file = os.path.join(TMP_DIR, 'file.bin')
        self.server.response['get.data'] = img_data

        g = build_grab()
        g.go(self.server.get_url())
        g.response.save(temp_file)
        self.assertEqual(open(temp_file, 'rb').read(), img_data)

    def test_save_hash(self):
        "Test `Response.save_hash` method."
        img_data = open(IMG_FILE, 'rb').read()
        self.server.response['get.data'] = img_data

        g = build_grab()
        g.go(self.server.get_url())
        path = g.response.save_hash(self.server.get_url(), TMP_DIR)
        test_data = open(os.path.join(TMP_DIR, path), 'rb').read()
        self.assertEqual(test_data, img_data)

    def test_custom_charset(self):
        self.server.response['get.data'] = u'<html><head><meta '\
            u'http-equiv="Content-Type" content="text/html; '\
            u'charset=utf8;charset=cp1251" /></head><body>'\
            u'<h1>крокодил</h1></body></html>'.encode('utf-8')
        g = build_grab()
        g.setup(document_charset='utf-8')
        g.go(self.server.get_url())
        self.assertTrue(u'крокодил' in g.response.unicode_body())

    def test_xml_declaration(self):
        """
        unicode_body() should return HTML with xml declaration (if it
        exists in original HTML)
        """
        self.server.response['get.data'] = """<?xml version="1.0" encoding="UTF-8"?>
        <html><body><h1>тест</h1></body></html>
        """
        g = build_grab()
        g.go(self.server.get_url())
        ubody = g.response.unicode_body()
        self.assertTrue(u'тест' in ubody)
        self.assertTrue('<?xml' in ubody)
