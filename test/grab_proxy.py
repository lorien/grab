# coding: utf-8
from test.util import build_grab, temp_file
from test.util import (BaseGrabTestCase, TEST_SERVER_PORT,
                       EXTRA_PORT1, EXTRA_PORT2)
import six
from grab.proxylist import BaseProxySource

ADDRESS = '127.0.0.1'
PROXY1 = '%s:%d' % (ADDRESS, TEST_SERVER_PORT)
PROXY2 = '%s:%d' % (ADDRESS, EXTRA_PORT1)
PROXY3 = '%s:%d' % (ADDRESS, EXTRA_PORT2)


class TestProxy(BaseGrabTestCase):
    def test_proxy_option(self):
        grab = build_grab()

        grab.setup(proxy=PROXY1, proxy_type='http', debug=True)
        self.server.response['get.data'] = '123'

        grab.go('http://yandex.ru')
        self.assertEqual(b'123', grab.response.body)
        self.assertEqual('yandex.ru', self.server.request['headers']['host'])

    def test_deprecated_setup_proxylist(self):
        with temp_file() as tmp_file:
            grab = build_grab()
            open(tmp_file, 'w').write(PROXY1)
            grab.load_proxylist(tmp_file, 'text_file')
            self.server.response['get.data'] = '123'
            grab.change_proxy()
            grab.go('http://yandex.ru')
            self.assertEqual(b'123', grab.response.body)
            self.assertEqual('yandex.ru',
                             self.server.request['headers']['host'])

    def test_load_proxylist(self):
        with temp_file() as tmp_file:
            content = '%s\n%s\n%s' % (PROXY1, PROXY2, PROXY3)
            open(tmp_file, 'w').write(content)

            # By default auto_change is True
            grab = build_grab()
            grab.load_proxylist(tmp_file, 'text_file')
            self.assertEqual(grab.config['proxy_auto_change'], True)
            servers = set()
            for _ in six.moves.range(10):
                grab.go('http://yandex.ru')
                servers.add(grab.config['proxy'])

            self.assertTrue(len(servers) > 1)

            # Disable auto_change
            # By default auto_init is True
            grab = build_grab()
            grab.load_proxylist(tmp_file, 'text_file', auto_change=False)
            self.assertEqual(grab.config['proxy_auto_change'], False)
            servers = set()
            for _ in six.moves.range(10):
                grab.go('http://yandex.ru')
                servers.add(grab.config['proxy'])
            self.assertEqual(len(servers), 1)

            # Disable auto_change
            # Disable auto_init
            # Proxylist will not be used by default
            grab = build_grab()
            grab.load_proxylist(tmp_file, 'text_file', auto_change=False,
                                auto_init=False)
            self.assertEqual(grab.config['proxy_auto_change'], False)
            grab.go(self.server.get_url())
            self.assertEqual(grab.config['proxy'], None)

    def test_change_proxy(self):
        with temp_file() as tmp_file:
            grab = build_grab()
            grab.change_proxy()
            self.assertEqual(grab.config['proxy'], None)

            grab = build_grab()
            with open(tmp_file, 'w') as out:
                for num in six.moves.range(10):
                    out.write('server-%d:777\n' % num)
            grab.load_proxylist(tmp_file, 'text_file', auto_init=False,
                                auto_change=False)
            self.assertEqual(grab.config['proxy'], None)

            grab.load_proxylist(tmp_file, 'text_file', auto_init=False,
                                auto_change=True)
            self.assertEqual(grab.config['proxy'], None)

            grab.load_proxylist(tmp_file, 'text_file', auto_init=True,
                                auto_change=False)
            # pylint: disable=unsupported-membership-test
            self.assertTrue('server-' in grab.config['proxy'])
            # pylint: enable=unsupported-membership-test

    def test_list_proxysource(self):
        grab = build_grab()
        items = [PROXY1, PROXY2]
        grab.proxylist.load_list(items)
        grab.go('http://yandex.ru')
        self.assertEqual(self.server.request['headers']['host'], 'yandex.ru')
        self.assertTrue(grab.doc.headers['listen-port'] in
                        (str(TEST_SERVER_PORT), str(EXTRA_PORT1)))

    def test_custom_proxysource(self):
        class CustomProxySource(BaseProxySource):
            def load_raw_data(self):
                return '\n'.join((PROXY1, PROXY2 + ':foo:bar'))

        grab = build_grab()
        grab.setup(proxy_auto_change=False)
        grab.proxylist.set_source(CustomProxySource())
        grab.change_proxy(random=False)
        grab.go('http://yandex.ru')
        self.assertEqual(self.server.request['headers']['host'], 'yandex.ru')
        self.assertEqual(grab.doc.headers['listen-port'],
                         str(TEST_SERVER_PORT))
        grab.change_proxy(random=False)
        grab.go('http://yandex.ru')
        self.assertEqual(self.server.request['headers']['host'], 'yandex.ru')
        self.assertEqual(grab.doc.headers['listen-port'], str(EXTRA_PORT1))

    def test_baseproxysource_constructor_arguments(self):
        src = BaseProxySource()
        self.assertEqual(src.config, {'proxy_type': 'http',
                                      'proxy_userpwd': None})
        src = BaseProxySource(proxy_type='socks')
        self.assertEqual(src.config, {'proxy_type': 'socks',
                                      'proxy_userpwd': None})
        src = BaseProxySource(proxy_userpwd='foo:bar')
        self.assertEqual(src.config, {'proxy_type': 'http',
                                      'proxy_userpwd': 'foo:bar'})
        src = BaseProxySource(foo='bar')
        self.assertEqual(src.config, {'proxy_type': 'http',
                                      'proxy_userpwd': None,
                                      'foo': 'bar'})

    def test_global_proxy_userpwd_argument(self):
        grab = build_grab()
        items = [PROXY1]
        grab.proxylist.load_list(items)
        self.assertEqual(grab.proxylist.get_next_proxy().username, None)

        grab.proxylist.load_list(items, proxy_userpwd='foo:bar')
        proxy = grab.proxylist.get_next_proxy()
        self.assertEqual(proxy.username, 'foo')
        self.assertEqual(proxy.password, 'bar')

        items = [PROXY1 + ':admin:test', PROXY2]
        grab.proxylist.load_list(items, proxy_userpwd='foo:bar')
        proxy = grab.proxylist.get_next_proxy()
        self.assertEqual(proxy.username, 'admin')
        self.assertEqual(proxy.password, 'test')

    def test_global_proxy_type_argument(self):
        grab = build_grab()
        items = [PROXY1]

        grab.proxylist.load_list(items)
        proxy = grab.proxylist.get_next_proxy()
        self.assertEqual(proxy.proxy_type, 'http')

        grab.proxylist.load_list(items, proxy_type='socks')
        proxy = grab.proxylist.get_next_proxy()
        self.assertEqual(proxy.proxy_type, 'socks')

    def test_setup_with_proxyline(self):
        grab = build_grab()
        grab.setup_with_proxyline('1.1.1.1:8080')
        self.assertEqual(grab.config['proxy'], '1.1.1.1:8080')
        self.assertEqual(grab.config['proxy_userpwd'], None)
        self.assertEqual(grab.config['proxy_type'], 'http')

    def test_setup_with_proxyline_custom_proxy_type(self):
        grab = build_grab()
        grab.setup_with_proxyline('1.1.1.1:8080', proxy_type='socks')
        self.assertEqual(grab.config['proxy'], '1.1.1.1:8080')
        self.assertEqual(grab.config['proxy_userpwd'], None)
        self.assertEqual(grab.config['proxy_type'], 'socks')

    def test_setup_with_proxyline_userpwd(self):
        grab = build_grab()
        grab.setup_with_proxyline('1.1.1.1:8080:user:pass')
        self.assertEqual(grab.config['proxy'], '1.1.1.1:8080')
        self.assertEqual(grab.config['proxy_userpwd'], 'user:pass')
        self.assertEqual(grab.config['proxy_type'], 'http')
