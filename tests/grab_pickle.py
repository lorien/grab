import pickle

from six.moves.queue import Queue
from test_server import Response

from tests.util import BaseGrabTestCase
from tests.util import build_grab


class TestGrab(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    # def test_pickling(self):
    #    """
    #    Test that Grab instance could be pickled and unpickled.
    #    """

    #    grab = build_grab()
    #    self.server.add_response(
    #        Response(data=(b'<form><textarea name="text">the cat</textarea></form>'))
    #    )
    #    grab.go(self.server.get_url())
    #    grab.doc.set_input("text", "foobar")
    #    data = pickle.dumps(grab, pickle.HIGHEST_PROTOCOL)

    #    def func(pickled_grab, resultq):
    #        grab2 = pickle.loads(pickled_grab)
    #        text = grab2.doc.select("//textarea").text()
    #        resultq.put(text)

    #    result_queue = Queue()
    #    func(data, result_queue)

    #    text = result_queue.get(block=True, timeout=1)
    #    self.assertEqual(text, "the cat")
