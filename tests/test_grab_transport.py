from grab import HttpClient
from grab.smart_transport import SmartTransport
from tests.util import BaseTestCase


class TestTransportTestCase(BaseTestCase):
    def test_default_transport(self) -> None:
        grab = HttpClient()
        self.assertTrue(isinstance(grab.transport, SmartTransport))
