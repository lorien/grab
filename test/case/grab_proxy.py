# coding: utf-8
from unittest import TestCase

from grab import Grab, GrabMisuseError
from test.util import build_grab, TMP_FILE
from test.server import SERVER

from grab.util.py3k_support import *

PROXY1 = 'localhost:%d' % SERVER.PORT
PROXY2 = 'localhost:%d' % SERVER.EXTRA_PORT1
PROXY3 = 'localhost:%d' % SERVER.EXTRA_PORT2

class TestProxy(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_proxy_option(self):
        g = build_grab()

        g.setup(proxy=PROXY1, proxy_type='http', debug=True)
        SERVER.RESPONSE['get'] = '123'

        g.go('http://yandex.ru')
        self.assertEqual(b'123', g.response.body)
        self.assertEqual('yandex.ru', SERVER.REQUEST['headers']['host'])

    def test_deprecated_setup_proxylist(self):
        g = build_grab()
        open(TMP_FILE, 'w').write(PROXY1)
        g.load_proxylist(TMP_FILE, 'text_file')
        SERVER.RESPONSE['get'] = '123'
        g.change_proxy()
        g.go('http://yandex.ru')
        self.assertEqual(b'123', g.response.body)
        self.assertEqual('yandex.ru', SERVER.REQUEST['headers']['host'])

    def test_load_proxylist(self):
        content = '%s\n%s\n%s' % (PROXY1, PROXY2, PROXY3)
        open(TMP_FILE, 'w').write(content)

        # By default auto_change is True
        g = build_grab()
        g.load_proxylist(TMP_FILE, 'text_file')
        self.assertEqual(g.config['proxy_auto_change'], True)
        servers = set()
        for x in xrange(10):
            g.go('http://yandex.ru')
            servers.add(g.config['proxy'])

        self.assertTrue(len(servers) > 1)

        # Disable auto_change
        # By default auto_init is True
        g = build_grab()
        g.load_proxylist(TMP_FILE, 'text_file', auto_change=False)
        self.assertEqual(g.config['proxy_auto_change'], False)
        servers = set()
        for x in xrange(10):
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
        g.go(SERVER.BASE_URL)
        self.assertEqual(g.config['proxy'], None)

    #def test_memory_proxylist(self):
        #g = build_grab()
        #server_list = ['localhost:%d' % PORT1]
        #g.setup_proxylist(server_list=server_list, proxy_type='http',
                          #auto_init=True)
        #SERVER.RESPONSE['get'] = '123'
        #g.go('http://yandex.ru')
        #self.assertEqual('123', g.response.body)
        #self.assertEqual('yandex.ru', SERVER.REQUEST['headers']['host'])

    def test_change_proxy(self):
        g = build_grab()
        with open(TMP_FILE, 'w') as out:
            for x in xrange(10):
                out.write('server-%d:777\n' % x)

        g.load_proxylist(TMP_FILE, 'text_file', auto_init=False, auto_change=False)
        self.assertEqual(g.config['proxy'], None)

        g.load_proxylist(TMP_FILE, 'text_file', auto_init=False, auto_change=True)
        self.assertEqual(g.config['proxy'], None)

        g.load_proxylist(TMP_FILE, 'text_file', auto_init=True, auto_change=False)
        self.assertTrue('server-' in g.config['proxy'])

    def test_proxylist_api(self):
        g = build_grab()
        #self.assertRaises(GrabMisuseError,
                          #lambda: g.setup_proxylist(proxy_file='foo', server_list=[]))
