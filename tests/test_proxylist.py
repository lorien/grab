from proxylist import ProxyList
from test_server import Response

from tests.util import BaseTestCase, temp_file

DEFAULT_PLIST_DATA = b"1.1.1.1:8080\n1.1.1.2:8080\n"


class ProxyListTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    def generate_plist_file(self, path: str, data: bytes = DEFAULT_PLIST_DATA) -> str:
        with open(path, "wb") as out:
            out.write(data)
        return path

    def test_file_proxy_source(self) -> None:
        with temp_file() as path:
            self.generate_plist_file(path)
            plist = ProxyList.from_local_file(path)
            self.assertEqual(2, plist.size())

    def test_web_proxy_source(self) -> None:
        self.server.add_response(Response(data=DEFAULT_PLIST_DATA))
        plist = ProxyList.from_network_file(self.server.get_url())
        self.assertEqual(2, plist.size())

    def test_get_next_proxy(self) -> None:
        with temp_file() as path:
            self.generate_plist_file(path, b"foo:1\nbar:1")
            plist = ProxyList.from_local_file(path)
            self.assertEqual(plist.get_next_server().host, "foo")
            self.assertEqual(plist.get_next_server().host, "bar")
            self.assertEqual(plist.get_next_server().host, "foo")

            plist = ProxyList.from_local_file(path)
            self.assertEqual(plist.get_next_server().host, "foo")
