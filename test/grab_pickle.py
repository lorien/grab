# coding: utf-8
from unittest import TestCase
import cPickle as pickle

from grab import Grab
from .tornado_util import SERVER

class TestGrab(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_pickling(self):
        """
        Test that Grab instance could be pickled and unpickled.
        """

        g = Grab()
        SERVER.RESPONSE['get'] = '<form><textarea name="text">the cat</textarea></form>'
        g.go(SERVER.BASE_URL)
        g.set_input('text', 'foobar')
        data = pickle.dumps(g)
        
        g2 = pickle.loads(data)
        self.assertEqual(g2.doc.select('//textarea').text(), 'the cat')
