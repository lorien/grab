from __future__ import annotations

from typing import Any

from test_server import Response, TestServer

from grab import Document, HttpRequest
from grab.spider import Spider, Task
from tests.util import ADDRESS, BaseTestCase, temp_file

# from proxylist import ProxyServer
# from proxylist.base import BaseProxySource


class SimpleSpider(Spider):
    def task_baz(self, doc: Document, _task: Task) -> None:
        self.collect_runtime_event("ports", str(int(doc.headers.get("Listen-Port", 0))))


class TestSpiderProxyCase(BaseTestCase):
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

    # def test_setup_proxylist(self):
    #    with temp_file() as proxy_file:
    #        for item in self.extra_servers.values():
    #            item["server"].add_response(Response(), count=-1)
    #        content = "\n".join(x["proxy"] for x in self.extra_servers.values())
    #        with open(proxy_file, "w", encoding="utf-8") as out:
    #            out.write(content)
    #        # Simple test, one task
    #        bot = SimpleSpider(thread_number=1)
    #        bot.load_proxylist(proxy_file, "text_file")
    #        bot.add_task(Task("baz", "http://yandex.ru"))
    #        bot.run()
    #        serv = [
    #            x["server"]
    #            for x in self.extra_servers.values()
    #            if x["server"].request_is_done()
    #        ][0]
    #        self.assertEqual(serv.request.headers.get("host"), "yandex.ru")
    #        self.assertEqual(1, len(set(bot.runtime_events["ports"])))

    # def test_setup_proxylist2(self):
    #    with temp_file() as proxy_file:
    #        for item in self.extra_servers.values():
    #            item["server"].add_response(Response(), count=-1)
    #        content = "\n".join(x["proxy"] for x in self.extra_servers.values())
    #        with open(proxy_file, "w", encoding="utf-8") as out:
    #            out.write(content)

    #        # By default auto_change is True
    #        bot = SimpleSpider(thread_number=1)
    #        bot.load_proxylist(proxy_file, "text_file")
    #        for _ in range(10):
    #            bot.add_task(
    #                Task(name="baz", request=HttpRequest("GET", "http://yandex.ru"))
    #            )
    #        bot.run()

    #        servers = [
    #            x["server"]
    #            for x in self.extra_servers.values()
    #            if x["server"].request_is_done()
    #        ]
    #        for serv in servers:
    #            self.assertEqual(serv.request.headers.get("host"), "yandex.ru")
    #        self.assertTrue(len(set(bot.runtime_events["ports"])) > 1)

    # def test_setup_proxylist4(self):
    #    with temp_file() as proxy_file:
    #        for item in self.extra_servers.values():
    #            item["server"].add_response(Response())
    #        content = "\n".join(x["proxy"] for x in self.extra_servers.values())
    #        with open(proxy_file, "w", encoding="utf-8") as out:
    #            out.write(content)

    #        # Disable auto_change
    #        # By default auto_init is True
    #        bot = SimpleSpider(thread_number=1)
    #        bot.load_proxylist(proxy_file, "text_file", auto_change=False)
    #        for _ in range(1):
    #            bot.add_task(
    #                Task(name="baz", request=HttpRequest("GET", "http://yandex.ru"))
    #            )
    #        bot.run()

    #        servers = [
    #            x["server"]
    #            for x in self.extra_servers.values()
    #            if x["server"].request_is_done()
    #        ]
    #        for serv in servers:
    #            self.assertEqual(serv.request.headers.get("host"), "yandex.ru")
    #        self.assertEqual(len(servers), 1)
    #        self.assertEqual(1, len(set(bot.runtime_events["ports"])))

    def test_setup_proxylist5(self) -> None:
        with temp_file() as proxy_file:
            self.server.add_response(Response(), count=10)
            for item in self.extra_servers.values():
                item["server"].add_response(Response())
            content = "\n".join(x["proxy"] for x in self.extra_servers.values())
            with open(proxy_file, "w", encoding="utf-8") as out:
                out.write(content)
            # Disable auto_change
            # Disable auto_init
            # Proxylist will not be used by default
            bot = SimpleSpider(thread_number=1)
            bot.load_proxylist(
                proxy_file, "text_file", auto_change=False, auto_init=False
            )
            for _ in range(10):
                bot.add_task(
                    Task(name="baz", request=HttpRequest(self.server.get_url()))
                )
            bot.run()

            self.assertEqual(
                self.server.request.headers.get("host"),
                "{}:{}".format(ADDRESS, self.server.port),
            )
            self.assertEqual(1, len(set(bot.runtime_events["ports"])))
            self.assertEqual(bot.runtime_events["ports"][0], str(self.server.port))

    # def test_spider_custom_proxy_source(self):
    #    proxy_port = self.server.port
    #    self.server.add_response(Response())

    #    class TestSpider(Spider):
    #        def task_page(self, grab, unused_task):
    #            self.collect_runtime_event(
    #                "ports", int(grab.doc.headers.get("Listen-Port", 0))
    #            )

    #    class CustomProxySource(BaseProxySource):
    #        def get_servers_list(self):
    #            return [
    #                ProxyServer(ADDRESS, proxy_port, None, None, "http"),
    #            ]

    #        def load_raw_data(self):
    #            return None

    #    bot = TestSpider()
    #    bot.load_proxylist(CustomProxySource())
    #    bot.add_task(Task("page", url="http://yandex.ru/"))
    #    bot.run()

    #    self.assertEqual(self.server.request.headers.get("host"), "yandex.ru")
    #    self.assertEqual(set(bot.runtime_events["ports"]), {self.server.port})
