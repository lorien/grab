# coding: utf-8
from test.util import build_grab, TMP_FILE
from test.util import (BaseGrabTestCase, TEST_SERVER_PORT,
                       EXTRA_PORT1, EXTRA_PORT2)
from test_server import TestServer
import six
from grab.proxylist import BaseProxySource

ADDRESS = '127.0.0.1'
PROXY1 = '%s:%d' % (ADDRESS, TEST_SERVER_PORT)
PROXY2 = '%s:%d' % (ADDRESS, EXTRA_PORT1)
PROXY3 = '%s:%d' % (ADDRESS, EXTRA_PORT2)


class TestProxy(BaseGrabTestCase):
    def test_proxy_option(self):
        g = build_grab()

        g.setup(proxy=PROXY1, proxy_type='http', debug=True)
        self.server.response['get.data'] = '123'

        g.go('http://yandex.ru')
        self.assertEqual(b'123', g.response.body)
        self.assertEqual('yandex.ru', self.server.request['headers']['host'])

    def test_deprecated_setup_proxylist(self):
        g = build_grab()
        open(TMP_FILE, 'w').write(PROXY1)
        g.load_proxylist(TMP_FILE, 'text_file')
        self.server.response['get.data'] = '123'
        g.change_proxy()
        g.go('http://yandex.ru')
        self.assertEqual(b'123', g.response.body)
        self.assertEqual('yandex.ru', self.server.request['headers']['host'])

    def test_load_proxylist(self):
        content = '%s\n%s\n%s' % (PROXY1, PROXY2, PROXY3)
        open(TMP_FILE, 'w').write(content)

        # By default auto_change is True
        g = build_grab()
        g.load_proxylist(TMP_FILE, 'text_file')
        self.assertEqual(g.config['proxy_auto_change'], True)
        servers = set()
        for x in six.moves.range(10):
            g.go('http://yandex.ru')
            servers.add(g.config['proxy'])

        self.assertTrue(len(servers) > 1)

        # Disable auto_change
        # By default auto_init is True
        g = build_grab()
        g.load_proxylist(TMP_FILE, 'text_file', auto_change=False)
        self.assertEqual(g.config['proxy_auto_change'], False)
        servers = set()
        for x in six.moves.range(10):
            g.go('http://yandex.ru')
            servers.add(g.config['proxy'])
        self.assertEqual(len(servers), 1)

        # Disable auto_change
        # Disable auto_init
        # Proxylist will not be used by default
        g = build_grab()
        g.load_proxylist(TMP_FILE, 'text_file', auto_change=False,
                         auto_init=False)
        self.assertEqual(g.config['proxy_auto_change'], False)
        g.go(self.server.get_url())
        self.assertEqual(g.config['proxy'], None)

    def test_change_proxy(self):
        g = build_grab()
        g.change_proxy()
        self.assertEqual(g.config['proxy'], None)

        g = build_grab()
        with open(TMP_FILE, 'w') as out:
            for x in six.moves.range(10):
                out.write('server-%d:777\n' % x)
        g.load_proxylist(TMP_FILE, 'text_file', auto_init=False,
                         auto_change=False)
        self.assertEqual(g.config['proxy'], None)

        g.load_proxylist(TMP_FILE, 'text_file', auto_init=False,
                         auto_change=True)
        self.assertEqual(g.config['proxy'], None)

        g.load_proxylist(TMP_FILE, 'text_file', auto_init=True,
                         auto_change=False)
        self.assertTrue('server-' in g.config['proxy'])

    def test_list_proxysource(self):
        g = build_grab()
        items = [PROXY1, PROXY2]
        g.proxylist.load_list(items)
        g.go('http://yandex.ru')
        self.assertEqual(self.server.request['headers']['host'], 'yandex.ru')
        self.assertTrue(g.doc.headers['listen-port'] in 
                        (str(TEST_SERVER_PORT), str(EXTRA_PORT1)))

    def test_custom_proxysource(self):
        class CustomProxySource(BaseProxySource):
            def load_raw_data(self):
                return '\n'.join((PROXY1, PROXY2 + ':foo:bar'))

        g = build_grab()
        g.setup(proxy_auto_change=False)
        g.proxylist.set_source(CustomProxySource())
        g.use_next_proxy()
        g.go('http://yandex.ru')
        self.assertEqual(self.server.request['headers']['host'], 'yandex.ru')
        self.assertEqual(g.doc.headers['listen-port'], str(TEST_SERVER_PORT))
        g.use_next_proxy()
        g.go('http://yandex.ru')
        self.assertEqual(self.server.request['headers']['host'], 'yandex.ru')
        self.assertEqual(g.doc.headers['listen-port'], str(EXTRA_PORT1))

    def test_baseproxysource_constructor_arguments(self):
        ps = BaseProxySource()
        self.assertEqual(ps.config, {'proxy_type': 'http', 'proxy_userpwd': None})
        ps = BaseProxySource(proxy_type='socks')
        self.assertEqual(ps.config, {'proxy_type': 'socks', 'proxy_userpwd': None})
        ps = BaseProxySource(proxy_userpwd='foo:bar')
        self.assertEqual(ps.config, {'proxy_type': 'http', 'proxy_userpwd': 'foo:bar'})
        ps = BaseProxySource(foo='bar')
        self.assertEqual(ps.config, {'proxy_type': 'http', 'proxy_userpwd': None,
                                     'foo': 'bar'})

    def test_global_proxy_userpwd_argument(self):
        g = build_grab()
        items = [PROXY1]
        g.proxylist.load_list(items)
        self.assertEquals(g.proxylist.get_next_proxy().username, None)

        g.proxylist.load_list(items, proxy_userpwd='foo:bar')
        proxy = g.proxylist.get_next_proxy()
        self.assertEquals(proxy.username, 'foo')
        self.assertEquals(proxy.password, 'bar')

        items = [PROXY1 + ':admin:test', PROXY2]
        g.proxylist.load_list(items, proxy_userpwd='foo:bar')
        proxy = g.proxylist.get_next_proxy()
        self.assertEquals(proxy.username, 'admin')
        self.assertEquals(proxy.password, 'test')

    def test_global_proxy_type_argument(self):
        g = build_grab()
        items = [PROXY1]

        g.proxylist.load_list(items)
        proxy = g.proxylist.get_next_proxy()
        self.assertEquals(proxy.proxy_type, 'http')

        g.proxylist.load_list(items, proxy_type='socks')
        proxy = g.proxylist.get_next_proxy()
        self.assertEquals(proxy.proxy_type, 'socks')
