from unittest import TestCase

from grab import HttpClient
from grab.transport import Urllib3Transport
from grab.types import resolve_grab_entity, resolve_transport_entity


class ResolveHttpClientEntityTestCase(TestCase):
    def test_resolve_grab_entity_default(self):
        class SuperHttpClient(HttpClient):
            pass

        self.assertTrue(
            isinstance(resolve_grab_entity(None, SuperHttpClient), SuperHttpClient)
        )

    def test_resolve_grab_entity_none_nodefault(self):
        with self.assertRaises(TypeError):
            resolve_grab_entity(None, None)

    def test_resolve_grab_entity_instance(self):
        class SuperHttpClient(HttpClient):
            pass

        self.assertTrue(
            isinstance(
                resolve_grab_entity(SuperHttpClient(), HttpClient), SuperHttpClient
            )
        )

    def test_resolve_grab_entity_class(self):
        class SuperHttpClient(HttpClient):
            pass

        self.assertTrue(
            isinstance(
                resolve_grab_entity(SuperHttpClient, HttpClient), SuperHttpClient
            )
        )


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
            isinstance(
                resolve_transport_entity(SuperTransport(), HttpClient), SuperTransport
            )
        )

    def test_resolve_transport_entity_class(self):
        class SuperTransport(Urllib3Transport):
            pass

        self.assertTrue(
            isinstance(
                resolve_transport_entity(SuperTransport, HttpClient), SuperTransport
            )
        )
