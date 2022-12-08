from typing import Dict

from grab import Grab
from grab.proxylist import BaseProxySource, Proxy
from grab.spider import Spider, Task
from test_server import Response, TestServer
from tests.util import ADDRESS, BaseGrabTestCase, build_spider, temp_file


class SimpleSpider(Spider):
    def task_baz(self, grab, unused_task):
        self.stat.collect("ports", int(grab.doc.headers.get("Listen-Port", 0)))


class TestSpiderProxyCase(BaseGrabTestCase):
    extra_servers: Dict[int, Dict]

    @classmethod
    def setUpClass(cls):
        super(TestSpiderProxyCase, cls).setUpClass()
        cls.extra_servers = {}
        for _ in range(3):
            serv = TestServer(address=ADDRESS, port=0)
            serv.start()
            cls.extra_servers[serv.port] = {
                "server": serv,
                "proxy": "%s:%d" % (ADDRESS, serv.port),
            }

    @classmethod
    def tearDownClass(cls):
        super(TestSpiderProxyCase, cls).tearDownClass()
        for item in cls.extra_servers.values():
            item["server"].stop()

    def setUp(self):
        super().setUp()
        for item in self.extra_servers.values():
            item["server"].reset()

    def test_setup_proxylist(self):
        with temp_file() as proxy_file:
            for item in self.extra_servers.values():
                item["server"].add_response(Response(), count=-1)
            content = "\n".join(x["proxy"] for x in self.extra_servers.values())
            with open(proxy_file, "w", encoding="utf-8") as out:
                out.write(content)
            # Simple test, one task
            bot = build_spider(SimpleSpider, thread_number=1)
            bot.load_proxylist(proxy_file, "text_file")
            bot.setup_queue()
            bot.add_task(Task("baz", grab=Grab(url="http://yandex.ru", debug=True)))
            bot.run()
            serv = [
                x["server"]
                for x in self.extra_servers.values()
                if x["server"].request_is_done()
            ][0]
            self.assertEqual(serv.request.headers.get("host"), "yandex.ru")
            self.assertEqual(1, len(set(bot.stat.collections["ports"])))

    def test_setup_proxylist2(self):
        with temp_file() as proxy_file:
            for item in self.extra_servers.values():
                item["server"].add_response(Response(), count=-1)
            content = "\n".join(x["proxy"] for x in self.extra_servers.values())
            with open(proxy_file, "w", encoding="utf-8") as out:
                out.write(content)

            # By default auto_change is True
            bot = build_spider(SimpleSpider, thread_number=1)
            bot.load_proxylist(proxy_file, "text_file")
            bot.setup_queue()
            for _ in range(10):
                bot.add_task(Task("baz", "http://yandex.ru"))
            bot.run()

            servers = [
                x["server"]
                for x in self.extra_servers.values()
                if x["server"].request_is_done()
            ]
            for serv in servers:
                self.assertEqual(serv.request.headers.get("host"), "yandex.ru")
            self.assertTrue(len(set(bot.stat.collections["ports"])) > 1)

    def test_setup_proxylist4(self):
        with temp_file() as proxy_file:
            for item in self.extra_servers.values():
                item["server"].add_response(Response())
            content = "\n".join(x["proxy"] for x in self.extra_servers.values())
            with open(proxy_file, "w", encoding="utf-8") as out:
                out.write(content)

            # Disable auto_change
            # By default auto_init is True
            bot = build_spider(SimpleSpider, thread_number=1)
            bot.load_proxylist(proxy_file, "text_file", auto_change=False)
            bot.setup_queue()
            for _ in range(1):
                bot.add_task(Task("baz", "http://yandex.ru"))
            bot.run()

            servers = [
                x["server"]
                for x in self.extra_servers.values()
                if x["server"].request_is_done()
            ]
            for serv in servers:
                self.assertEqual(serv.request.headers.get("host"), "yandex.ru")
            self.assertEqual(len(servers), 1)
            self.assertEqual(1, len(set(bot.stat.collections["ports"])))

    def test_setup_proxylist5(self):
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
            bot = build_spider(SimpleSpider, thread_number=1)
            bot.load_proxylist(
                proxy_file, "text_file", auto_change=False, auto_init=False
            )
            bot.setup_queue()
            for _ in range(10):
                bot.add_task(Task("baz", self.server.get_url()))
            bot.run()

            self.assertEqual(
                self.server.request.headers.get("host"),
                "%s:%s" % (ADDRESS, self.server.port),
            )
            self.assertEqual(1, len(set(bot.stat.collections["ports"])))
            self.assertEqual(bot.stat.collections["ports"][0], self.server.port)

    def test_spider_custom_proxy_source(self):
        proxy_port = self.server.port
        self.server.add_response(Response())

        class TestSpider(Spider):
            def task_page(self, grab, unused_task):
                self.stat.collect("ports", int(grab.doc.headers.get("Listen-Port", 0)))

        class CustomProxySource(BaseProxySource):
            def load(self):
                return [
                    Proxy(ADDRESS, proxy_port, None, None, "http"),
                ]

            def load_raw_data(self):
                return None

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.load_proxylist(CustomProxySource())
        bot.add_task(Task("page", url="http://yandex.ru/"))
        bot.run()

        self.assertEqual(self.server.request.headers.get("host"), "yandex.ru")
        self.assertEqual(set(bot.stat.collections["ports"]), set([self.server.port]))
