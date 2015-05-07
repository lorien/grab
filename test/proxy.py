# coding: utf-8
from test.util import build_grab, get_temp_file
from test.util import BaseGrabTestCase

from grab import Grab
from grab.proxylist import ProxyList

DEFAULT_PLIST_DATA = \
    '1.1.1.1:8080\n'\
    '1.1.1.2:8080\n'


class GrabProxyTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def generate_plist_file(self, data=DEFAULT_PLIST_DATA):
        path = get_temp_file()
        with open(path, 'w') as out:
            out.write(data)
        return path

    def test_no_proxy_list(self):
        g = build_grab()
        self.assertEqual(0, g.proxylist.size())


class ProxyListTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def generate_plist_file(self, data=DEFAULT_PLIST_DATA):
        path = get_temp_file()
        with open(path, 'w') as out:
            out.write(data)
        return path

    def test_basic(self):
        pl = ProxyList()
        self.assertEqual(0, pl.size())


    def test_file_proxy_source(self):
        pl = ProxyList()
        path = self.generate_plist_file()
        pl.load_file(path)
        self.assertEqual(2, pl.size())

    def test_web_proxy_source(self):
        pl = ProxyList()
        self.server.response['data'] = DEFAULT_PLIST_DATA
        pl.load_url(self.server.get_url())
        self.assertEqual(2, pl.size())

    def test_get_next_proxy(self):
        pl = ProxyList()
        path = self.generate_plist_file('foo:1\nbar:1')
        pl.load_file(path)
        self.assertEqual(pl.get_next_proxy().host, 'foo')
        self.assertEqual(pl.get_next_proxy().host, 'bar')
        self.assertEqual(pl.get_next_proxy().host, 'foo')
        pl.load_file(path)
        self.assertEqual(pl.get_next_proxy().host, 'foo')
