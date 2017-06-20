from test_server import TestServer
import six

from tests.util import (
    BaseGrabTestCase, TEST_SERVER_PORT,
    build_spider, ADDRESS, temp_file
)
from grab import Grab
from grab.spider import Spider, Task
from grab.proxylist import BaseProxySource, Proxy


class SimpleSpider(Spider):
    def task_baz(self, grab, unused_task):
        self.stat.collect('ports',
                          int(grab.doc.headers.get('Listen-Port', 0)))


class TestSpiderProxyCase(BaseGrabTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestSpiderProxyCase, cls).setUpClass()
        cls.extra_servers = {}
        for _ in range(3):
            serv = TestServer(address=ADDRESS)
            serv.start()
            cls.extra_servers[serv.port] = {
                'server': serv,
                'proxy': '%s:%d' % (ADDRESS, serv.port),
            }

    @classmethod
    def tearDownClass(cls):
        super(TestSpiderProxyCase, cls).tearDownClass()
        for item in cls.extra_servers.values():
            item['server'].stop()

    def setUp(self):
        super(TestSpiderProxyCase, self).setUp()
        for item in self.extra_servers.values():
            item['server'].reset()

    def test_setup_proxylist(self):
        with temp_file() as proxy_file:
            content = '\n'.join(x['proxy'] for x in
                                self.extra_servers.values())
            with open(proxy_file, 'w') as out:
                out.write(content)
            # Simple test, one task
            bot = build_spider(SimpleSpider, thread_number=1)
            bot.load_proxylist(proxy_file, 'text_file')
            bot.setup_queue()
            bot.add_task(Task('baz', grab=Grab(url='http://yandex.ru',
                                               debug=True)))
            bot.run()
            serv = [x['server'] for x in self.extra_servers.values()
                    if x['server'].request['done']][0]
            self.assertEqual(serv.request['headers']['host'], 'yandex.ru')
            self.assertEqual(1, len(set(bot.stat.collections['ports'])))

    def test_setup_proxylist2(self):
        with temp_file() as proxy_file:
            content = '\n'.join(x['proxy'] for x in
                                self.extra_servers.values())
            with open(proxy_file, 'w') as out:
                out.write(content)

            # By default auto_change is True
            bot = build_spider(SimpleSpider, thread_number=1)
            bot.load_proxylist(proxy_file, 'text_file')
            bot.setup_queue()
            for _ in six.moves.range(10):
                bot.add_task(Task('baz', 'http://yandex.ru'))
            bot.run()

            servers = [x['server'] for x in self.extra_servers.values()
                       if x['server'].request['done']]
            for serv in servers:
                self.assertEqual(serv.request['headers']['host'], 'yandex.ru')
            self.assertTrue(len(set(bot.stat.collections['ports'])) > 1)

    def test_setup_proxylist4(self):
        with temp_file() as proxy_file:
            content = '\n'.join(x['proxy'] for x in
                                self.extra_servers.values())
            with open(proxy_file, 'w') as out:
                out.write(content)

            # Disable auto_change
            # By default auto_init is True
            bot = build_spider(SimpleSpider, thread_number=1)
            bot.load_proxylist(proxy_file, 'text_file', auto_change=False)
            bot.setup_queue()
            for _ in six.moves.range(1):
                bot.add_task(Task('baz', 'http://yandex.ru'))
            bot.run()

            servers = [x['server'] for x in self.extra_servers.values()
                       if x['server'].request['done']]
            for serv in servers:
                self.assertEqual(serv.request['headers']['host'], 'yandex.ru')
            self.assertEqual(len(servers), 1)
            self.assertEqual(1, len(set(bot.stat.collections['ports'])))

    def test_setup_proxylist5(self):
        with temp_file() as proxy_file:
            content = '\n'.join(x['proxy'] for x in
                                self.extra_servers.values())
            with open(proxy_file, 'w') as out:
                out.write(content)
            # Disable auto_change
            # Disable auto_init
            # Proxylist will not be used by default
            bot = build_spider(SimpleSpider, thread_number=1)
            bot.load_proxylist(proxy_file, 'text_file',
                               auto_change=False, auto_init=False)
            bot.setup_queue()
            for _ in six.moves.range(10):
                bot.add_task(Task('baz', self.server.get_url()))
            bot.run()

            self.assertEqual(self.server.request['headers'].get('host'),
                             '%s:%s' % (ADDRESS, self.server.port))
            self.assertEqual(1, len(set(bot.stat.collections['ports'])))
            self.assertEqual(bot.stat.collections['ports'][0],
                             self.server.port)

    def test_spider_custom_proxy_source(self):
        proxy_port = self.server.port

        class TestSpider(Spider):
            def task_page(self, grab, unused_task):
                self.stat.collect(
                    'ports', int(grab.doc.headers.get('Listen-Port', 0)))

        class CustomProxySource(BaseProxySource):
            def load(self):
                return [
                    Proxy(ADDRESS, proxy_port, None, None, 'http'),
                ]

            def load_raw_data(self):
                return None

        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.load_proxylist(CustomProxySource())
        bot.add_task(Task('page', url='http://yandex.ru/'))
        bot.run()

        self.assertEqual(self.server.request['headers']['host'], 'yandex.ru')
        self.assertEqual(set(bot.stat.collections['ports']),
                         set([TEST_SERVER_PORT]))
