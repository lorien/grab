# coding: utf-8
from tests.util import build_grab, temp_file
from tests.util import BaseGrabTestCase

from grab.proxylist import ProxyList

DEFAULT_PLIST_DATA = \
    '1.1.1.1:8080\n'\
    '1.1.1.2:8080\n'


class GrabProxyTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_no_proxy_list(self):
        grab = build_grab()
        self.assertEqual(0, grab.proxylist.size())


class ProxyListTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def generate_plist_file(self, path, data=DEFAULT_PLIST_DATA):
        with open(path, 'w') as out:
            out.write(data)
        return path

    def test_basic(self):
        plist = ProxyList()
        self.assertEqual(0, plist.size())

    def test_file_proxy_source(self):
        with temp_file() as path:
            plist = ProxyList()
            self.generate_plist_file(path)
            plist.load_file(path)
            self.assertEqual(2, plist.size())

    def test_web_proxy_source(self):
        plist = ProxyList()
        self.server.response['data'] = DEFAULT_PLIST_DATA
        plist.load_url(self.server.get_url())
        self.assertEqual(2, plist.size())

    def test_get_next_proxy(self):
        with temp_file() as path:
            plist = ProxyList()
            self.generate_plist_file(path, 'foo:1\nbar:1')
            plist.load_file(path)
            self.assertEqual(plist.get_next_proxy().host, 'foo')
            self.assertEqual(plist.get_next_proxy().host, 'bar')
            self.assertEqual(plist.get_next_proxy().host, 'foo')
            plist.load_file(path)
            self.assertEqual(plist.get_next_proxy().host, 'foo')
