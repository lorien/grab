import six

from grab import Grab
from grab.proxylist import BaseProxySource, Proxy
from grab.spider import Spider, Task
from test_server import Request, Response, TestServer
from tests.util import (
    ADDRESS,
    TEST_SERVER_PORT,
    BaseGrabTestCase,
    build_spider,
    temp_file,
)

NUM_PROXY_SERVERS = 3


class SimpleSpider(Spider):
    def task_baz(self, grab, unused_task):
        self.stat.collect("ports", int(grab.doc.headers.get("Listen-Port", 0)))


class TestSpiderProxyCase(BaseGrabTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestSpiderProxyCase, cls).setUpClass()
        cls.extra_servers = {}
        for cnt in range(NUM_PROXY_SERVERS):
            serv = TestServer(address=ADDRESS, port=TEST_SERVER_PORT + 1 + cnt)
            serv.start()
            cls.extra_servers[serv.port] = {
                "server": serv,
                "proxy": "%s:%d" % (ADDRESS, serv.port),
            }

    def add_response_bulk(self, resp, count):
        # type: (Response) -> None
        self.server.add_response(Response(), count=count)
        for srv_item in self.extra_servers.values():
            srv_item["server"].add_response(Response(), count=count)

    @classmethod
    def tearDownClass(cls):
        super(TestSpiderProxyCase, cls).tearDownClass()
        for item in cls.extra_servers.values():
            item["server"].stop()

    def setUp(self):
        super(TestSpiderProxyCase, self).setUp()
        for item in self.extra_servers.values():
            item["server"].reset()

    def test_setup_proxylist(self):
        self.add_response_bulk(Response(), count=1)
        with temp_file() as proxy_file:
            content = "\n".join(x["proxy"] for x in self.extra_servers.values())
            with open(proxy_file, "w") as out:
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
            self.assertEqual(serv.get_request().headers.get("host"), "yandex.ru")
            self.assertEqual(1, len(set(bot.stat.collections["ports"])))

    def test_setup_proxylist2(self):
        self.add_response_bulk(Response(), count=10)
        with temp_file() as proxy_file:
            content = "\n".join(x["proxy"] for x in self.extra_servers.values())
            with open(proxy_file, "w") as out:
                out.write(content)

            # By default auto_change is True
            bot = build_spider(SimpleSpider, thread_number=1)
            bot.load_proxylist(proxy_file, "text_file")
            bot.setup_queue()
            for _ in six.moves.range(10):
                bot.add_task(Task("baz", "http://yandex.ru"))
            bot.run()

            servers = [
                x["server"]
                for x in self.extra_servers.values()
                if x["server"].request_is_done()
            ]
            for serv in servers:
                self.assertEqual(serv.get_request().headers.get("host"), "yandex.ru")
            self.assertTrue(len(set(bot.stat.collections["ports"])) > 1)

    def test_setup_proxylist4(self):
        self.add_response_bulk(Response(), count=1)
        with temp_file() as proxy_file:
            content = "\n".join(x["proxy"] for x in self.extra_servers.values())
            with open(proxy_file, "w") as out:
                out.write(content)

            # Disable auto_change
            # By default auto_init is True
            bot = build_spider(SimpleSpider, thread_number=1)
            bot.load_proxylist(proxy_file, "text_file", auto_change=False)
            bot.setup_queue()
            for _ in six.moves.range(1):
                bot.add_task(Task("baz", "http://yandex.ru"))
            bot.run()

            servers = [
                x["server"]
                for x in self.extra_servers.values()
                if x["server"].request_is_done()
            ]
            for serv in servers:
                self.assertEqual(serv.get_request().headers.get("host"), "yandex.ru")
            self.assertEqual(len(servers), 1)
            self.assertEqual(1, len(set(bot.stat.collections["ports"])))

    def test_setup_proxylist5(self):
        self.add_response_bulk(Response(), count=10)
        with temp_file() as proxy_file:
            content = "\n".join(x["proxy"] for x in self.extra_servers.values())
            with open(proxy_file, "w") as out:
                out.write(content)
            # Disable auto_change
            # Disable auto_init
            # Proxylist will not be used by default
            bot = build_spider(SimpleSpider, thread_number=1)
            bot.load_proxylist(
                proxy_file, "text_file", auto_change=False, auto_init=False
            )
            bot.setup_queue()
            for _ in six.moves.range(10):
                bot.add_task(Task("baz", self.server.get_url()))
            bot.run()

            req = self.server.get_request()

            self.assertEqual(
                req.headers.get("host"), "%s:%s" % (ADDRESS, self.server.port)
            )
            self.assertEqual(1, len(set(bot.stat.collections["ports"])))
            self.assertEqual(bot.stat.collections["ports"][0], self.server.port)

    def test_spider_custom_proxy_source(self):
        self.add_response_bulk(Response(), count=1)
        proxy_port = self.server.port

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

        req = self.server.get_request()

        self.assertEqual(req.headers.get("host"), "yandex.ru")
        self.assertEqual(set(bot.stat.collections["ports"]), set([TEST_SERVER_PORT]))
