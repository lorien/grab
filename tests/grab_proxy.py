# coding: utf-8
from tests.util import build_grab, temp_file
from tests.util import BaseGrabTestCase
import six
from grab.proxylist import BaseProxySource
from test_server import TestServer

ADDRESS = '127.0.0.1'


class TestProxy(BaseGrabTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestProxy, cls).setUpClass()
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
        super(TestProxy, cls).tearDownClass()
        for item in cls.extra_servers.values():
            item['server'].stop()

    def setUp(self):
        super(TestProxy, self).setUp()
        for item in self.extra_servers.values():
            item['server'].reset()

    def test_proxy_option(self):
        grab = build_grab()

        proxy = '%s:%s' % (ADDRESS, self.server.port)
        grab.setup(proxy=proxy, proxy_type='http', debug=True)
        self.server.response['data'] = '123'

        grab.go('http://yandex.ru')
        self.assertEqual(b'123', grab.doc.body)
        self.assertEqual('yandex.ru', self.server.request['headers']['host'])

    def test_deprecated_setup_proxylist(self):
        with temp_file() as tmp_file:
            proxy = '%s:%s' % (ADDRESS, self.server.port)
            grab = build_grab()
            with open(tmp_file, 'w') as out:
                out.write(proxy)
            grab.proxylist.load_file(tmp_file)
            self.server.response['get.data'] = '123'
            grab.change_proxy()
            grab.go('http://yandex.ru')
            self.assertEqual(b'123', grab.doc.body)
            self.assertEqual('yandex.ru',
                             self.server.request['headers']['host'])

    def test_load_proxylist(self):
        with temp_file() as tmp_file:
            content = '\n'.join(x['proxy'] for x in
                                self.extra_servers.values())
            with open(tmp_file, 'w') as out:
                out.write(content)

            # By default auto_change is True
            grab = build_grab()
            grab.proxylist.load_file(tmp_file)
            self.assertEqual(grab.config['proxy_auto_change'], True)
            servers = set()
            for _ in six.moves.range(10):
                grab.go('http://yandex.ru')
                servers.add(grab.config['proxy'])

            self.assertTrue(len(servers) > 1)

            # Disable auto_change
            # Change proxy manually
            grab = build_grab()
            grab.proxylist.load_file(tmp_file)
            grab.setup(proxy_auto_change=False)
            grab.change_proxy()
            self.assertEqual(grab.config['proxy_auto_change'], False)
            # TODO: probably call proxy change manually
            servers = set()
            for _ in six.moves.range(10):
                grab.go('http://yandex.ru')
                servers.add(grab.config['proxy'])
            self.assertEqual(len(servers), 1)

            # Disable auto_change
            # By default auto_init is True
            # Proxylist will not be used by default
            grab = build_grab()
            grab.proxylist.load_file(tmp_file)
            grab.setup(proxy_auto_change=False)
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
            grab.proxylist.load_file(tmp_file)
            grab.setup(proxy_auto_change=False)
            self.assertEqual(grab.config['proxy'], None)

            grab.proxylist.load_file(tmp_file)
            self.assertEqual(grab.config['proxy'], None)

            grab.proxylist.load_file(tmp_file)
            grab.setup(proxy_auto_change=False)
            grab.change_proxy()
            # pylint: disable=unsupported-membership-test
            self.assertTrue('server-' in grab.config['proxy'])
            # pylint: enable=unsupported-membership-test

    def test_list_proxysource(self):
        grab = build_grab()
        items = [x['proxy'] for x in self.extra_servers.values()]
        grab.proxylist.load_list(items)
        grab.go('http://yandex.ru')
        servers = [x['server'] for x in self.extra_servers.values()
                   if x['server'].request['done']]
        for serv in servers:
            self.assertEqual(serv.request['headers']['host'], 'yandex.ru')
        self.assertTrue(grab.doc.headers['listen-port'] in
                        map(str, self.extra_servers))

    def test_custom_proxysource(self):
        extra_servers = list(self.extra_servers.values())

        class CustomProxySource(BaseProxySource):
            def load_raw_data(self):
                return '\n'.join(x['proxy'] for x in extra_servers)

        grab = build_grab()
        grab.setup(proxy_auto_change=False)
        grab.proxylist.set_source(CustomProxySource())
        grab.change_proxy(random=False)
        grab.go('http://yandex.ru')
        serv = extra_servers[0]['server']
        self.assertEqual((serv.request['headers']['host']), 'yandex.ru')
        self.assertEqual(grab.doc.headers['listen-port'], str(serv.port))
        grab.change_proxy(random=False)
        grab.go('http://yandex.ru')
        serv = extra_servers[1]['server']
        self.assertEqual(serv.request['headers']['host'], 'yandex.ru')
        self.assertEqual(grab.doc.headers['listen-port'], str(serv.port))

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
        items = ['localhost:1']
        grab.proxylist.load_list(items)
        self.assertEqual(grab.proxylist.get_next_proxy().username, None)

        grab.proxylist.load_list(items, proxy_userpwd='foo:bar')
        proxy = grab.proxylist.get_next_proxy()
        self.assertEqual(proxy.username, 'foo')
        self.assertEqual(proxy.password, 'bar')

        items = ['localhost:1' + ':admin:test', 'localhost:2']
        grab.proxylist.load_list(items, proxy_userpwd='foo:bar')
        proxy = grab.proxylist.get_next_proxy()
        self.assertEqual(proxy.username, 'admin')
        self.assertEqual(proxy.password, 'test')

    def test_global_proxy_type_argument(self):
        grab = build_grab()
        items = ['localhost:1']

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
