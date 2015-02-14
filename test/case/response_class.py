# coding: utf-8
from __future__ import absolute_import
from unittest import TestCase
from grab import Grab, DataNotFound, GrabMisuseError
import os.path

from test.util import TEST_DIR, TMP_DIR, build_grab
from test.server import SERVER

HTML = """
Hello world
"""

IMG_FILE = os.path.join(TEST_DIR, 'files', 'yandex.png')

class TestResponse(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_save(self):
        """
        Test `Response.save` method.
        """
        
        img_data = open(IMG_FILE, 'rb').read()
        temp_file = os.path.join(TMP_DIR, 'file.bin')
        SERVER.RESPONSE['get'] = img_data

        g = build_grab()
        g.go(SERVER.BASE_URL)
        g.response.save(temp_file)
        self.assertEqual(open(temp_file, 'rb').read(), img_data)

    def test_save_hash(self):
        """
        Test `Response.save_hash` method.
        """
        
        img_data = open(IMG_FILE, 'rb').read()
        SERVER.RESPONSE['get'] = img_data

        g = build_grab()
        g.go(SERVER.BASE_URL)
        path = g.response.save_hash(SERVER.BASE_URL, TMP_DIR)
        test_data = open(os.path.join(TMP_DIR, path), 'rb').read()
        self.assertEqual(test_data, img_data)

    def test_custom_charset(self):
        SERVER.RESPONSE['get'] = u'<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf8;charset=cp1251" /></head><body><h1>крокодил</h1></body></html>'.encode('utf-8')
        g = build_grab()
        g.setup(document_charset='utf-8')
        g.go(SERVER.BASE_URL)
        self.assertTrue(u'крокодил' in g.response.unicode_body())

    def test_xml_declaration(self):
        """
        unicode_body() should return HTML with xml declaration (if it
        exists in original HTML)
        """
        SERVER.RESPONSE['get'] = """<?xml version="1.0" encoding="UTF-8"?>
        <html><body><h1>тест</h1></body></html>
        """
        g = build_grab()
        g.go(SERVER.BASE_URL)
        ubody = g.response.unicode_body()
        self.assertTrue(u'тест' in ubody)
        self.assertTrue('<?xml' in ubody)
