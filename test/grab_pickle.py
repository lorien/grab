# coding: utf-8
from unittest import TestCase
import cPickle as pickle

from grab import Grab
from util import FakeServerThread, BASE_URL, RESPONSE

class TestGrab(TestCase):
    def setUp(self):
        FakeServerThread().start()

    def test_pickling(self):
        g = Grab()
        RESPONSE['get'] = '<form><textarea name="text">the cat</textarea></form>'
        g.go(BASE_URL)
        g.set_input('text', 'foobar')
        data = pickle.dumps(g)
        
        g2 = pickle.loads(data)
        self.assertEqual(g2.xpath_text('//textarea'), 'the cat')
