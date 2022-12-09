from urllib.request import urlopen

from test_server import Response

from tests.util import BaseGrabTestCase


class RawTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_response(self):
        def callback():
            return b"HTTP/1.1 200 OK\n\nFOO"

        self.server.add_response(Response(raw_callback=callback))
        with urlopen(self.server.get_url()) as inp:
            self.assertEqual(inp.read(), b"FOO")

    def test_sequential_responses(self):
        def callback1():
            return b"HTTP/1.1 200 OK\n\nFOO"

        self.server.add_response(Response(raw_callback=callback1))
        with urlopen(self.server.get_url()) as inp:
            self.assertEqual(inp.read(), b"FOO")

        def callback2():
            return b"HTTP/1.1 200 OK\n\nBAR"

        self.server.add_response(Response(raw_callback=callback2))
        with urlopen(self.server.get_url()) as inp:
            self.assertEqual(inp.read(), b"BAR")
