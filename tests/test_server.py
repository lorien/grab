from urllib.request import urlopen

from test_server import Response

from tests.util import BaseTestCase


class RawTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    def test_response(self) -> None:
        def callback() -> bytes:
            return b"HTTP/1.1 200 OK\n\nFOO"

        self.server.add_response(Response(raw_callback=callback))
        with urlopen(self.server.get_url()) as inp:
            self.assertEqual(inp.read(), b"FOO")

    def test_sequential_responses(self) -> None:
        def callback1() -> bytes:
            return b"HTTP/1.1 200 OK\n\nFOO"

        self.server.add_response(Response(raw_callback=callback1))
        with urlopen(self.server.get_url()) as inp:
            self.assertEqual(inp.read(), b"FOO")

        def callback2() -> bytes:
            return b"HTTP/1.1 200 OK\n\nBAR"

        self.server.add_response(Response(raw_callback=callback2))
        with urlopen(self.server.get_url()) as inp:
            self.assertEqual(inp.read(), b"BAR")
