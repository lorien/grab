from grab import HttpClient
from grab.transport import Urllib3Transport
from tests.util import BaseTestCase


class TestTransportTestCase(BaseTestCase):
    def test_default_transport(self) -> None:
        grab = HttpClient()
        self.assertTrue(isinstance(grab.transport, Urllib3Transport))
