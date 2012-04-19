# coding: utf-8
from unittest import TestCase

from grab import Grab, GrabMisuseError
from util import (FakeServerThread, RESPONSE, REQUEST, FAKE_SERVER_PORT,
                  GRAB_TRANSPORT)

class TestProxy(TestCase):
    def setUp(self):
        FakeServerThread().start()

    def test_proxy(self):
        g = Grab(transport=GRAB_TRANSPORT)
        proxy = 'localhost:%d' % FAKE_SERVER_PORT 
        g.setup(proxy=proxy, proxy_type='http')
        RESPONSE['get'] = '123'
        g.go('http://yandex.ru')
        self.assertEqual('123', g.response.body)
        self.assertEqual('yandex.ru', REQUEST['headers']['host'])

    def test_file_proxylist(self):
        g = Grab(transport=GRAB_TRANSPORT)
        proxy = 'localhost:%d' % FAKE_SERVER_PORT 
        open('/tmp/__proxy.txt', 'w').write(proxy)
        g.setup_proxylist('/tmp/__proxy.txt', 'http')
        RESPONSE['get'] = '123'
        g.change_proxy()
        g.go('http://yandex.ru')
        self.assertEqual('123', g.response.body)
        self.assertEqual('yandex.ru', REQUEST['headers']['host'])

    def test_memory_proxylist(self):
        g = Grab(transport=GRAB_TRANSPORT)
        server_list = ['localhost:%d' % FAKE_SERVER_PORT]
        g.setup_proxylist(server_list=server_list, proxy_type='http',
                          auto_init=True)
        RESPONSE['get'] = '123'
        g.go('http://yandex.ru')
        self.assertEqual('123', g.response.body)
        self.assertEqual('yandex.ru', REQUEST['headers']['host'])

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
        self.assertRaises(GrabMisuseError,
                          lambda: g.setup_proxylist(proxy_file='foo', server_list=[]))
        self.assertRaises(GrabMisuseError,
                          lambda: g.setup_proxylist(proxy_file=None, server_list=None))
        self.assertRaises(GrabMisuseError,
                          lambda: g.setup_proxylist('foo', server_list=[]))
