from grab import Grab
from grab.error import GrabMisuseError
from grab.transport import Urllib3Transport
from tests.util import BaseGrabTestCase


class TestTransportTestCase(BaseGrabTestCase):
    def test_invalid_transport_invalid_alias(self):
        grab = Grab()
        with self.assertRaises(GrabMisuseError):
            grab.setup_transport("zzzzzzzzzz")

    def test_invalid_transport_invalid_path(self):
        grab = Grab()
        # AttributeError comes from setup_transport method
        with self.assertRaises(AttributeError):
            grab.setup_transport("tests.test_grab_transport.zzz")

    def test_invalid_transport_not_collable_or_string(self):
        grab = Grab()
        with self.assertRaises(GrabMisuseError):
            grab.setup_transport(13)

    def test_setup_transport_twice(self):
        transport = "urllib3"
        grab = Grab()
        grab.setup_transport(transport)
        with self.assertRaises(GrabMisuseError) as ex:
            grab.setup_transport(transport)
        self.assertTrue("Transport is already set up" in str(ex.exception))

    def test_setup_transport_none(self):
        grab = Grab()
        self.assertTrue(grab.transport is None)

        grab.setup_transport(None)
        self.assertEqual(grab.transport_param, "grab.transport.Urllib3Transport")

    def test_setup_transport_callable(self):
        grab = Grab()
        grab.setup_transport(Urllib3Transport)
        self.assertTrue(isinstance(grab.transport, Urllib3Transport))
