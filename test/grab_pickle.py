# coding: utf-8
from unittest import TestCase
try:
    import cPickle as pickle
except ImportError:
    import pickle
from multiprocessing import Process, Queue

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
        data = pickle.dumps(g, pickle.HIGHEST_PROTOCOL)

        def func(pickled_grab, resultq):
            g2 = pickle.loads(pickled_grab)
            text = g2.doc.select('//textarea').text()
            resultq.put(text)

        result_queue = Queue()
        p = Process(target=func, args=[data, result_queue])
        p.start()

        text = result_queue.get()
        self.assertEqual(text, 'the cat')
