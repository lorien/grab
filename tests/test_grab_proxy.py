from __future__ import annotations

from typing import Any

from test_server import Response, TestServer

from grab import request
from tests.util import BaseTestCase  # , temp_file

# from proxylist.source import BaseFileProxySource
# from proxylist import ProxyList


TestServer.__test__ = False  # make pytest do not explore it for test cases
ADDRESS = "127.0.0.1"


class TestProxy(BaseTestCase):
    extra_servers: dict[int, dict[str, Any]]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.extra_servers = {}
        for _ in range(3):
            serv = TestServer(address=ADDRESS, port=0)
            serv.start()
            assert serv.port is not None
            cls.extra_servers[serv.port] = {
                "server": serv,
                "proxy": "%s:%d" % (ADDRESS, serv.port),
            }

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        for item in cls.extra_servers.values():
            item["server"].stop()

    def setUp(self) -> None:
        super().setUp()
        for item in self.extra_servers.values():
            item["server"].reset()

    def test_proxy_option(self) -> None:
        self.server.add_response(Response(data=b"123"))
        proxy = "{}:{}".format(ADDRESS, self.server.port)
        doc = request("http://yandex.ru", proxy=proxy, proxy_type="http")
        self.assertEqual(b"123", doc.body)
        self.assertEqual("yandex.ru", self.server.request.headers.get("host"))

    # def test_deprecated_setup_proxylist(self):
    #    with temp_file() as tmp_file:
    #        proxy = "%s:%s" % (ADDRESS, self.server.port)
    #        with open(tmp_file, "w", encoding="utf-8") as out:
    #            out.write(proxy)
    #        grab.proxylist = ProxyList.from_local_file(tmp_file, proxy_type="http")
    #        self.server.add_response(Response(data=b"123"))
    #        grab.change_proxy()
    #        doc = request("http://yandex.ru")
    #        self.assertEqual(b"123", doc.body)
    #        self.assertEqual("yandex.ru", self.server.request.headers.get("host"))

    # def test_load_proxylist(self):
    #    with temp_file() as tmp_file:
    #        content = "\n".join(x["proxy"] for x in self.extra_servers.values())
    #        with open(tmp_file, "w", encoding="utf-8") as out:
    #            out.write(content)

    #        # By default auto_change is True
    #        grab.proxylist = ProxyList.from_local_file(tmp_file, proxy_type="http")
    #        self.assertEqual(grab.config["proxy_auto_change"], True)
    #        servers = set()
    #        for _ in range(10):
    #            request("http://yandex.ru")
    #            servers.add(grab.config["proxy"])

    #        self.assertTrue(len(servers) > 1)

    #        # Disable auto_change
    #        # Change proxy manually
    #        grab.proxylist = ProxyList.from_local_file(tmp_file, proxy_type="http")
    #        grab.setup(proxy_auto_change=False)
    #        grab.change_proxy()
    #        self.assertEqual(grab.config["proxy_auto_change"], False)
    #        # TODO: probably call proxy change manually
    #        servers = set()
    #        for _ in range(10):
    #            request("http://yandex.ru")
    #            servers.add(grab.config["proxy"])
    #        self.assertEqual(len(servers), 1)

    #        # Disable auto_change
    #        # By default auto_init is True
    #        # Proxylist will not be used by default
    #        grab.proxylist = ProxyList.from_local_file(tmp_file, proxy_type="http")
    #        grab.setup(proxy_auto_change=False)
    #        self.assertEqual(grab.config["proxy_auto_change"], False)
    #        request(self.server.get_url())
    #        self.assertEqual(grab.config["proxy"], None)

    # def test_change_proxy(self):
    #    with temp_file() as tmp_file:
    #        grab.change_proxy()
    #        self.assertEqual(grab.config["proxy"], None)
    #        with open(tmp_file, "w", encoding="utf-8") as out:
    #            for num in range(10):
    #                out.write("server-%d:777\n" % num)
    #        grab.proxylist = ProxyList.from_local_file(tmp_file, proxy_type="http")
    #        grab.setup(proxy_auto_change=False)
    #        self.assertEqual(grab.config["proxy"], None)

    #        grab.proxylist = ProxyList.from_local_file(tmp_file, proxy_type="http")
    #        self.assertEqual(grab.config["proxy"], None)

    #        grab.proxylist = ProxyList.from_local_file(tmp_file, proxy_type="http")
    #        grab.setup(proxy_auto_change=False)
    #        grab.change_proxy()
    #        self.assertTrue("server-" in grab.config["proxy"])

    # def test_list_proxysource(self):
    #    for item in self.extra_servers.values():
    #        item["server"].add_response(Response())
    #    items = [x["proxy"] for x in self.extra_servers.values()]

    #    grab.proxylist = ProxyList.from_lines_list(items, proxy_type="http")
    #    doc = request("http://yandex.ru")
    #    servers = [
    #        x["server"]
    #        for x in self.extra_servers.values()
    #        if x["server"].request_is_done()
    #    ]
    #    for serv in servers:
    #        self.assertEqual(serv.request.headers.get("host"), "yandex.ru")
    #    self.assertTrue(
    #        doc.headers.get("listen-port") in map(str, self.extra_servers)
    #    )

    # def test_custom_proxysource(self):
    #    extra_servers = list(self.extra_servers.values())
    #    for item in extra_servers:
    #        item["server"].add_response(Response(), count=-1)

    #    class CustomProxySource(BaseFileProxySource):
    #        def __init__(self, proxy_type):
    #            super().__init__(proxy_type=proxy_type)

    #        def load_content(self):
    #            return "\n".join(x["proxy"] for x in extra_servers)

    #    grab.setup(proxy_auto_change=False)
    #    grab.proxylist = ProxyList(CustomProxySource("http"))
    #    grab.change_proxy(random=False)
    #    doc = request("http://yandex.ru")
    #    serv = extra_servers[0]["server"]
    #    self.assertEqual((serv.request.headers.get("host")), "yandex.ru")
    #    self.assertEqual(doc.headers.get("listen-port"), str(serv.port))
    #    grab.change_proxy(random=False)
    #    doc = request("http://yandex.ru")
    #    serv = extra_servers[1]["server"]
    #    self.assertEqual(serv.request.headers.get("host"), "yandex.ru")
    #    self.assertEqual(doc.headers.get("listen-port"), str(serv.port))

    # def test_global_proxy_userpwd_argument(self):
    #    items = ["localhost:1"]
    #    grab.proxylist = ProxyList.from_lines_list(items)
    #    self.assertEqual(grab.proxylist.get_next_server().username, None)

    #    grab.proxylist = ProxyList.from_lines_list(items, proxy_auth=("foo", "bar"))
    #    proxy = grab.proxylist.get_next_server()
    #    self.assertEqual(proxy.username, "foo")
    #    self.assertEqual(proxy.password, "bar")

    #    items = ["localhost:1" + ":admin:test", "localhost:2"]
    #    grab.proxylist = ProxyList.from_lines_list(items, proxy_auth=("foo", "bar"))
    #    proxy = grab.proxylist.get_next_server()
    #    self.assertEqual(proxy.username, "admin")
    #    self.assertEqual(proxy.password, "test")

    # def test_default_proxy_type_argument(self):
    #    items = ["localhost:1"]

    #    grab.proxylist = ProxyList.from_lines_list(items)
    #    proxy = grab.proxylist.get_next_server()
    #    self.assertEqual(proxy.proxy_type, None)

    #    grab.proxylist = ProxyList.from_lines_list(items, proxy_type="socks")
    #    proxy = grab.proxylist.get_next_server()
    #    self.assertEqual(proxy.proxy_type, "socks")
