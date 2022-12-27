from unittest import TestCase

from grab import HttpClient
from grab.transport import Urllib3Transport
from grab.util.types import resolve_entity


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
            resolve_entity(None, None, None)  # type: ignore

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
            isinstance(
                Urllib3Transport.resolve_entity(None, SuperTransport), SuperTransport
            )
        )

    def test_resolve_transport_entity_none_nodefault(self) -> None:
        with self.assertRaises(TypeError):
            Urllib3Transport.resolve_entity(None, None)  # type: ignore

    def test_resolve_transport_entity_instance(self) -> None:
        class SuperTransport(Urllib3Transport):
            pass

        self.assertTrue(
            isinstance(
                Urllib3Transport.resolve_entity(SuperTransport(), Urllib3Transport),
                SuperTransport,
            )
        )

    def test_resolve_transport_entity_class(self) -> None:
        class SuperTransport(Urllib3Transport):
            pass

        self.assertTrue(
            isinstance(
                Urllib3Transport.resolve_entity(SuperTransport, Urllib3Transport),
                SuperTransport,
            )
        )
