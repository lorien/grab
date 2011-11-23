# coding: utf-8
from unittest import TestCase

from grab import Grab
from util import FakeServerThread, BASE_URL, RESPONSE

class TestContentLimit(TestCase):
    def setUp(self):
        FakeServerThread().start()

    def test_nobody(self):
        g = Grab()
        g.setup(nobody=True)
        RESPONSE['get'] = 'foo'
        g.go(BASE_URL)
        self.assertEqual('', g.response.body)
        self.assertTrue(len(g.response.head) > 0)

    def test_body_maxsize(self):
        g = Grab()
        g.setup(body_maxsize=100)
        RESPONSE['get'] = 'x' * 10 ** 6
        g.go(BASE_URL)
        # Should be less 50kb
        self.assertTrue(len(g.response.body) < 50000)
