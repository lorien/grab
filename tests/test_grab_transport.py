from grab import Grab
from grab.transport import Urllib3Transport
from tests.util import BaseTestCase


class TestTransportTestCase(BaseTestCase):
    def test_default_transport(self):
        grab = Grab()
        self.assertTrue(isinstance(grab.transport, Urllib3Transport))
