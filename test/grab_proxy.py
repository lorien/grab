# coding: utf-8
from unittest import TestCase

from grab import Grab, GrabMisuseError
from util import (FakeServerThread, RESPONSE, REQUEST, FAKE_SERVER_PORT,
                  GRAB_TRANSPORT)

PORT1 = FAKE_SERVER_PORT
PORT2 = FAKE_SERVER_PORT + 1
PORT3 = FAKE_SERVER_PORT + 2
PROXY1 = 'localhost:%d' % PORT1
PROXY2 = 'localhost:%d' % PORT2
PROXY3 = 'localhost:%d' % PORT3

class TestProxy(TestCase):
    def setUp(self):
        FakeServerThread(port=PORT1).start()
        FakeServerThread(port=PORT2).start()
        FakeServerThread(port=PORT3).start()

    def test_proxy_option(self):
        g = Grab(transport=GRAB_TRANSPORT)

        g.setup(proxy=PROXY1, proxy_type='http')
        RESPONSE['get'] = '123'

        g.go('http://yandex.ru')
        self.assertEqual('123', g.response.body)
        self.assertEqual('yandex.ru', REQUEST['headers']['host'])

    def test_deprecated_setup_proxylist(self):
        g = Grab(transport=GRAB_TRANSPORT)
        open('/tmp/__proxy.txt', 'w').write(PROXY1)
        g.setup_proxylist('/tmp/__proxy.txt', 'http')
        RESPONSE['get'] = '123'
        g.change_proxy()
        g.go('http://yandex.ru')
        self.assertEqual('123', g.response.body)
        self.assertEqual('yandex.ru', REQUEST['headers']['host'])

    def test_load_proxylist(self):
        content = '%s\n%s\n%s' % (PROXY1, PROXY2, PROXY3)
        open('/tmp/__proxy.txt', 'w').write(content)

        # By default auto_change is True
        g = Grab(transport=GRAB_TRANSPORT)
        g.load_proxylist('/tmp/__proxy.txt', 'text_file')
        self.assertEqual(g.config['proxy_auto_change'], True)
        servers = set()
        for x in xrange(10):
            g.go('http://yandex.ru')
            servers.add(g.config['proxy'])

        self.assertTrue(len(servers) > 1)

        # Disable auto_change
        # By default auto_init is True
        g = Grab(transport=GRAB_TRANSPORT)
        g.load_proxylist('/tmp/__proxy.txt', 'text_file', auto_change=False)
        self.assertEqual(g.config['proxy_auto_change'], False)
        servers = set()
        for x in xrange(10):
            g.go('http://yandex.ru')
            servers.add(g.config['proxy'])
        self.assertEqual(len(servers), 1)

        # Disable auto_change
        # Disable auto_init
        # Proxylist will not be used by default
        g = Grab(transport=GRAB_TRANSPORT)
        g.load_proxylist('/tmp/__proxy.txt', 'text_file', auto_change=False,
                         auto_init=False)
        self.assertEqual(g.config['proxy_auto_change'], False)
        g.go('http://yandex.ru')
        self.assertEqual(g.config['proxy'], None)

    #def test_memory_proxylist(self):
        #g = Grab(transport=GRAB_TRANSPORT)
        #server_list = ['localhost:%d' % PORT1]
        #g.setup_proxylist(server_list=server_list, proxy_type='http',
                          #auto_init=True)
        #RESPONSE['get'] = '123'
        #g.go('http://yandex.ru')
        #self.assertEqual('123', g.response.body)
        #self.assertEqual('yandex.ru', REQUEST['headers']['host'])

    def test_change_proxy(self):
        g = Grab(transport=GRAB_TRANSPORT)
        with open('/tmp/__proxy.txt', 'w') as out:
            for x in xrange(10):
                out.write('server-%d:777\n' % x)

        g.setup_proxylist('/tmp/__proxy.txt', 'http', auto_init=False, auto_change=False)
        self.assertEqual(g.config['proxy'], None)

        g.setup_proxylist('/tmp/__proxy.txt', 'http', auto_init=False, auto_change=True)
        self.assertEqual(g.config['proxy'], None)

        g.setup_proxylist('/tmp/__proxy.txt', 'http', auto_init=True, auto_change=False)
        self.assertTrue('server-' in g.config['proxy'])

    def test_proxylist_api(self):
        g = Grab(transport=GRAB_TRANSPORT)
        #self.assertRaises(GrabMisuseError,
                          #lambda: g.setup_proxylist(proxy_file='foo', server_list=[]))
        self.assertRaises(GrabMisuseError,
                          lambda: g.setup_proxylist(proxy_file=None, server_list=None))
        self.assertRaises(GrabMisuseError,
                          lambda: g.setup_proxylist('foo', server_list=[]))
