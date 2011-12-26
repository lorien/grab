# coding: utf-8
from unittest import TestCase

from grab import Grab
from util import FakeServerThread, RESPONSE, REQUEST, FAKE_SERVER_PORT

class TestProxy(TestCase):
    def setUp(self):
        FakeServerThread().start()

    def test_proxy(self):
        g = Grab()
        proxy = 'localhost:%d' % FAKE_SERVER_PORT 
        g.setup(proxy=proxy, proxy_type='http')
        RESPONSE['get'] = '123'
        g.go('http://yandex.ru')
        self.assertEqual('123', g.response.body)
        self.assertEqual('yandex.ru', REQUEST['headers']['host'])

    def test_proxylist(self):
        g = Grab()
        proxy = 'localhost:%d' % FAKE_SERVER_PORT 
        open('/tmp/__proxy.txt', 'w').write(proxy)
        g.setup_proxylist('/tmp/__proxy.txt', 'http')
        RESPONSE['get'] = '123'
        g.change_proxy()
        g.go('http://yandex.ru')
        self.assertEqual('123', g.response.body)
        self.assertEqual('yandex.ru', REQUEST['headers']['host'])
