# coding: utf-8
from __future__ import absolute_import
from unittest import TestCase
from grab import Grab, DataNotFound, GrabMisuseError
import os.path

from .util import (FakeServerThread, TEST_DIR, TMP_DIR,
                   RESPONSE, BASE_URL, GRAB_TRANSPORT)

HTML = """
Hello world
"""

IMG_FILE = os.path.join(TEST_DIR, 'files', 'yandex.png')

class TestResponse(TestCase):
    def setUp(self):
        FakeServerThread().start()

    def test_save(self):
        """
        Test `Response.save` method.
        """
        
        img_data = open(IMG_FILE, 'rb').read()
        temp_file = os.path.join(TMP_DIR, 'file.bin')
        RESPONSE['get'] = img_data

        g = Grab(transport=GRAB_TRANSPORT)
        g.go(BASE_URL)
        g.response.save(temp_file)
        self.assertEqual(open(temp_file, 'rb').read(), img_data)

    def test_save_hash(self):
        """
        Test `Response.save_hash` method.
        """
        
        img_data = open(IMG_FILE, 'rb').read()
        RESPONSE['get'] = img_data

        g = Grab(transport=GRAB_TRANSPORT)
        g.go(BASE_URL)
        path = g.response.save_hash(BASE_URL, TMP_DIR)
        test_data = open(os.path.join(TMP_DIR, path), 'rb').read()
        self.assertEqual(test_data, img_data)

    def test_custom_charset(self):
        RESPONSE['get'] = u'<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf8;charset=cp1251" /></head><body><h1>крокодил</h1></body></html>'.encode('utf-8')
        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(document_charset='utf-8')
        g.go(BASE_URL)
        self.assertTrue(u'крокодил' in g.response.unicode_body())
