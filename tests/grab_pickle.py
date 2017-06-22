# coding: utf-8
try:
    import cPickle as pickle
except ImportError:
    import pickle
from multiprocessing import Queue

from tests.util import BaseGrabTestCase, exclude_grab_transport
from tests.util import build_grab


class TestGrab(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    @exclude_grab_transport('urllib3')
    def test_pickling(self):
        """
        Test that Grab instance could be pickled and unpickled.
        """

        grab = build_grab()
        self.server.response['get.data'] =\
            '<form><textarea name="text">the cat</textarea></form>'
        grab.go(self.server.get_url())
        grab.doc.set_input('text', 'foobar')
        data = pickle.dumps(grab, pickle.HIGHEST_PROTOCOL)

        def func(pickled_grab, resultq):
            grab2 = pickle.loads(pickled_grab)
            text = grab2.doc.select('//textarea').text()
            resultq.put(text)

        result_queue = Queue()
        # p = Process(target=func, args=[data, result_queue])
        # p.start()
        func(data, result_queue)

        text = result_queue.get(block=True, timeout=1)
        self.assertEqual(text, 'the cat')
