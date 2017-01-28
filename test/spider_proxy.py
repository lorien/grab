from test_server import TestServer
import six

from grab import Grab
from grab.spider import Spider, Task
from test.util import (BaseGrabTestCase, TEST_SERVER_PORT,
                       build_spider, ADDRESS, temp_file)
from grab.proxylist import BaseProxySource, Proxy

EXTRA_PORT1 = TEST_SERVER_PORT + 1
EXTRA_PORT2 = TEST_SERVER_PORT + 2
PROXY1 = '%s:%d' % (ADDRESS, TEST_SERVER_PORT)
PROXY2 = '%s:%d' % (ADDRESS, EXTRA_PORT1)
PROXY3 = '%s:%d' % (ADDRESS, EXTRA_PORT2)


class SimpleSpider(Spider):
    def task_baz(self, grab, task):
        self.stat.collect('ports',
                          int(grab.response.headers.get('Listen-Port', 0)))


class TestSpiderCase(BaseGrabTestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = TestServer(port=TEST_SERVER_PORT, address=ADDRESS,
                                extra_ports=[EXTRA_PORT1, EXTRA_PORT2])
        cls.server.start()

    def test_setup_proxylist(self):
        with temp_file() as proxy_file:
            content = '%s\n%s\n%s' % (PROXY1, PROXY2, PROXY3)
            open(proxy_file, 'w').write(content)
            # Simple test, one task
            bot = build_spider(SimpleSpider, thread_number=1)
            bot.load_proxylist(proxy_file, 'text_file')
            bot.setup_queue()
            bot.add_task(Task('baz', grab=Grab(url='http://yandex.ru',
                              debug=True)))
            bot.run()

            self.assertEqual(self.server.request['headers']['host'], 'yandex.ru')
            self.assertEqual(1, len(set(bot.stat.collections['ports'])))

    def test_setup_proxylist2(self):
        with temp_file() as proxy_file:
            content = '%s\n%s\n%s' % (PROXY1, PROXY2, PROXY3)
            open(proxy_file, 'w').write(content)

            # By default auto_change is True
            bot = build_spider(SimpleSpider, thread_number=1)
            bot.load_proxylist(proxy_file, 'text_file')
            bot.setup_queue()
            for _ in six.moves.range(10):
                bot.add_task(Task('baz', 'http://yandex.ru'))
            bot.run()

            self.assertEqual(self.server.request['headers']['host'], 'yandex.ru')
            self.assertTrue(len(set(bot.stat.collections['ports'])) > 1)

    def test_setup_proxylist3(self):
        with temp_file() as proxy_file:
            content = '%s\n%s\n%s' % (PROXY1, PROXY2, PROXY3)
            open(proxy_file, 'w').write(content)

            # WTF?????????????????
            # DO the same test with load_proxylist method
            bot = build_spider(SimpleSpider, thread_number=1)
            bot.load_proxylist(proxy_file, 'text_file')
            bot.setup_queue()
            for _ in six.moves.range(10):
                bot.add_task(Task('baz', 'http://yandex.ru'))
            bot.run()

            self.assertEqual(self.server.request['headers']['host'], 'yandex.ru')
            self.assertTrue(len(set(bot.stat.collections['ports'])) > 1)

    def test_setup_proxylist4(self):
        with temp_file() as proxy_file:
            content = '%s\n%s\n%s' % (PROXY1, PROXY2, PROXY3)
            open(proxy_file, 'w').write(content)

            # Disable auto_change
            # By default auto_init is True
            bot = build_spider(SimpleSpider, thread_number=1)
            bot.load_proxylist(proxy_file, 'text_file', auto_change=False)
            bot.setup_queue()
            for _ in six.moves.range(1):
                bot.add_task(Task('baz', 'http://yandex.ru'))
            bot.run()

            self.assertEqual(self.server.request['headers']['host'], 'yandex.ru')
            self.assertEqual(1, len(set(bot.stat.collections['ports'])))

    def test_setup_proxylist5(self):
        with temp_file() as proxy_file:
            content = '%s\n%s\n%s' % (PROXY1, PROXY2, PROXY3)
            open(proxy_file, 'w').write(content)
            # Disable auto_change
            # Disable auto_init
            # Proxylist will not be used by default
            bot = build_spider(SimpleSpider, thread_number=1)
            bot.load_proxylist(proxy_file, 'text_file',
                               auto_change=False, auto_init=False)
            bot.setup_queue()
            for x in six.moves.range(10):
                bot.add_task(Task('baz', self.server.get_url()))
            bot.run()

            self.assertEqual(self.server.request['headers'].get('host'),
                             '%s:%s' % (ADDRESS, self.server.port))
            self.assertEqual(1, len(set(bot.stat.collections['ports'])))
            self.assertEqual(bot.stat.collections['ports'][0], self.server.port)

    def test_spider_custom_proxy_source(self):
        class TestSpider(Spider):
            def task_page(self, grab, task):
                self.stat.collect(
                    'ports', int(grab.response.headers.get('Listen-Port', 0)))

        class CustomProxySource(BaseProxySource):
            def load(self):
                return [
                    Proxy(ADDRESS, TEST_SERVER_PORT, None, None, 'http'),
                ]


        bot = build_spider(TestSpider)
        bot.setup_queue()
        bot.load_proxylist(CustomProxySource())
        bot.add_task(Task('page', url='http://yandex.ru/'))
        bot.run()

        self.assertEqual(self.server.request['headers']['host'], 'yandex.ru')
        self.assertEqual(set(bot.stat.collections['ports']),
                         set([TEST_SERVER_PORT]))
