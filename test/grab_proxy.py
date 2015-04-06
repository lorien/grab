# coding: utf-8
from test.util import build_grab, TMP_FILE
from test.util import BaseGrabTestCase, TEST_SERVER_PORT
from test_server import TestServer
import six

ADDRESS = '127.0.0.1'
EXTRA_PORT1 = TEST_SERVER_PORT + 1
EXTRA_PORT2 = TEST_SERVER_PORT + 2
PROXY1 = '%s:%d' % (ADDRESS, TEST_SERVER_PORT)
PROXY2 = '%s:%d' % (ADDRESS, EXTRA_PORT1)
PROXY3 = '%s:%d' % (ADDRESS, EXTRA_PORT2)


class TestProxy(BaseGrabTestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = TestServer(port=TEST_SERVER_PORT,
                                extra_ports=[EXTRA_PORT1, EXTRA_PORT2])
        cls.server.start()

    def setUp(self):
        self.server.reset()

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
