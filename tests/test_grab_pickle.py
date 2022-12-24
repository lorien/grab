import pickle
from queue import Queue

from test_server import Response

from grab import request
from tests.util import BaseGrabTestCase


class TestGrab(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_pickling(self):
        """Test that Grab instance could be pickled and unpickled."""
        self.server.add_response(
            Response(data=(b'<form><textarea name="text">the cat</textarea></form>'))
        )
        doc = request(self.server.get_url())
        doc.set_input("text", "foobar")
        data = pickle.dumps(doc, pickle.HIGHEST_PROTOCOL)

        def func(pickled_doc, resultq):
            doc = pickle.loads(pickled_doc)
            text = doc.select("//textarea").text()
            resultq.put(text)

        result_queue = Queue()
        func(data, result_queue)

        text = result_queue.get(block=True, timeout=1)
        self.assertEqual(text, "the cat")
