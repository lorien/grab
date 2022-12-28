from test_server import Response

from grab import request
from grab.errors import GrabTimeoutError
from tests.util import BaseTestCase


class GrabTimeoutCase(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    def test_timeout_raises(self) -> None:
        self.server.add_response(Response(data=b"zzz", sleep=1))
        with self.assertRaises(GrabTimeoutError):
            request(timeout=0.1, url=self.server.get_url())

    def test_timeout_enough_to_complete(self) -> None:
        self.server.add_response(Response(data=b"zzz", sleep=0.5))
        request(timeout=2, url=self.server.get_url())
