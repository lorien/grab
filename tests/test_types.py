from unittest import TestCase

from grab import HttpClient
from grab.base import resolve_transport_entity
from grab.transport import Urllib3Transport
from grab.types import resolve_entity


class ResolveHttpClientEntityTestCase(TestCase):
    def test_resolve_entity_default(self) -> None:
        class SuperHttpClient(HttpClient):
            pass

        self.assertTrue(
            isinstance(
                resolve_entity(HttpClient, None, SuperHttpClient), SuperHttpClient
            )
        )

    def test_resolve_entity_none_nodefault(self) -> None:
        with self.assertRaises(TypeError):
            resolve_entity(None, None, None)

    def test_resolve_entity_instance(self) -> None:
        class SuperHttpClient(HttpClient):
            pass

        self.assertTrue(
            isinstance(
                resolve_entity(HttpClient, SuperHttpClient(), HttpClient),
                SuperHttpClient,
            )
        )

    def test_resolve_entity_class(self) -> None:
        class SuperHttpClient(HttpClient):
            pass

        self.assertTrue(
            isinstance(
                resolve_entity(HttpClient, SuperHttpClient, HttpClient), SuperHttpClient
            )
        )


class ResolveTransportEntityTestCase(TestCase):
    def test_resolve_transport_entity_default(self) -> None:
        class SuperTransport(Urllib3Transport):
            pass

        self.assertTrue(
            isinstance(resolve_transport_entity(None, SuperTransport), SuperTransport)
        )

    def test_resolve_transport_entity_none_nodefault(self) -> None:
        with self.assertRaises(TypeError):
            resolve_transport_entity(None, None)

    def test_resolve_transport_entity_instance(self) -> None:
        class SuperTransport(Urllib3Transport):
            pass

        self.assertTrue(
            isinstance(
                resolve_transport_entity(SuperTransport(), HttpClient), SuperTransport
            )
        )

    def test_resolve_transport_entity_class(self) -> None:
        class SuperTransport(Urllib3Transport):
            pass

        self.assertTrue(
            isinstance(
                resolve_transport_entity(SuperTransport, HttpClient), SuperTransport
            )
        )
