from unittest import TestCase

from grab.grab import Grab
from grab.transport import Urllib3Transport
from grab.types import resolve_grab_entity, resolve_transport_entity


class ResolveGrabEntityTestCase(TestCase):
    def test_resolve_grab_entity_default(self):
        class SuperGrab(Grab):
            pass

        self.assertTrue(isinstance(resolve_grab_entity(None, SuperGrab), SuperGrab))

    def test_resolve_grab_entity_none_nodefault(self):
        with self.assertRaises(TypeError):
            resolve_grab_entity(None, None)

    def test_resolve_grab_entity_instance(self):
        class SuperGrab(Grab):
            pass

        self.assertTrue(isinstance(resolve_grab_entity(SuperGrab(), Grab), SuperGrab))

    def test_resolve_grab_entity_class(self):
        class SuperGrab(Grab):
            pass

        self.assertTrue(isinstance(resolve_grab_entity(SuperGrab, Grab), SuperGrab))


class ResolveTransportEntityTestCase(TestCase):
    def test_resolve_transport_entity_default(self):
        class SuperTransport(Urllib3Transport):
            pass

        self.assertTrue(
            isinstance(resolve_transport_entity(None, SuperTransport), SuperTransport)
        )

    def test_resolve_transport_entity_none_nodefault(self):
        with self.assertRaises(TypeError):
            resolve_transport_entity(None, None)

    def test_resolve_transport_entity_instance(self):
        class SuperTransport(Urllib3Transport):
            pass

        self.assertTrue(
            isinstance(resolve_transport_entity(SuperTransport(), Grab), SuperTransport)
        )

    def test_resolve_transport_entity_class(self):
        class SuperTransport(Urllib3Transport):
            pass

        self.assertTrue(
            isinstance(resolve_transport_entity(SuperTransport, Grab), SuperTransport)
        )
