# coding: utf-8
from unittest import TestCase
from grab import Grab, DataNotFound, GrabMisuseError
import os.path

from tests.util import (FakeServerThread, prepare_temp_dir, TEST_DIR,
                        RESPONSE, BASE_URL)

HTML = """
Hello world
"""

IMG_FILE = os.path.join(TEST_DIR, 'files', 'yandex.png')

class TestHtmlForms(TestCase):
    def setUp(self):
        FakeServerThread().start()
        self.temp_dir = prepare_temp_dir()

    def test_response_save(self):
        """
        Test `Response.save` method.
        """
        
        # raise errors
        img_data = open(IMG_FILE, 'rb').read()
        temp_file = os.path.join(self.temp_dir, 'file.bin')
        RESPONSE['get'] = img_data

        g = Grab()
        g.go(BASE_URL)
        g.response.save(temp_file)
        self.assertEqual(open(temp_file, 'rb').read(), img_data)
