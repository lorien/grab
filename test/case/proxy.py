# coding: utf-8
from unittest import TestCase
#import string
import json
import re

from grab import Grab, GrabMisuseError
from test.util import TMP_FILE, GRAB_TRANSPORT, get_temp_file
from test.server import SERVER
from grab.proxy import ProxyList

DEFAULT_PLIST_DATA = \
    '1.1.1.1:8080\n'\
    '1.1.1.2:8080\n'

class GrabProxyTestCase(TestCase):
    def setUp(self):
        SERVER.reset()

    def generate_plist_file(self, data=DEFAULT_PLIST_DATA):
        path = get_temp_file()
        with open(path, 'w') as out:
            out.write(data)
        return path

    def test_basic(self):
        g = Grab(transport=GRAB_TRANSPORT)
        self.assertEqual(0, len(g.proxylist.proxy_list))


class ProxyListTestCase(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_basic(self):
        pl = ProxyList()
        self.assertEqual(0, len(pl.proxy_list))

    def generate_plist_file(self, data=DEFAULT_PLIST_DATA):
        path = get_temp_file()
        with open(path, 'w') as out:
            out.write(data)
        return path

    def test_file_source(self):
        pl = ProxyList()
        path = self.generate_plist_file()
        pl.set_source('file', location=path)
        self.assertEqual(2, len(pl.proxy_list))

    def test_remote_load(self):
        pl = ProxyList()
        SERVER.RESPONSE['get'] = DEFAULT_PLIST_DATA
        pl.set_source('url', url=SERVER.BASE_URL)
        self.assertEqual(2, len(pl.proxy_list))

    def test_accumulate_updates_basic(self):
        # test that all work with disabled accumulate_updates feature
        pl = ProxyList()
        path = self.generate_plist_file()
        pl.setup(accumulate_updates=False)
        pl.set_source('file', location=path)
        self.assertEqual(2, len(pl.proxy_list))

        # enable accumulate updates
        pl = ProxyList()
        pl.setup(accumulate_updates=True)
        path = self.generate_plist_file()
        pl.set_source('file', location=path)
        self.assertEqual(2, len(pl.proxy_list))

    def test_accumulate_updates_basic(self):
        pl = ProxyList()
        pl.setup(accumulate_updates=True)

        # load initial list
        path = self.generate_plist_file('foo:1\nbar:1')
        pl.set_source('file', location=path)
        self.assertEqual(2, len(pl.proxy_list))

        # load list with one new and one old proxies
        with open(path, 'w') as out:
            out.write('foo:1\nbaz:1')
        pl.reload(force=True)
        self.assertEqual(3, len(pl.proxy_list))

    def test_get_next_proxy(self):
        pl = ProxyList()
        path = self.generate_plist_file('foo:1\nbar:1')
        pl.set_source('file', location=path)
        self.assertEqual(pl.get_next_proxy().server, 'foo')
        self.assertEqual(pl.get_next_proxy().server, 'bar')
        self.assertEqual(pl.get_next_proxy().server, 'foo')
        pl.set_source('file', location=path)
        self.assertEqual(pl.get_next_proxy().server, 'foo')

    def test_get_next_proxy_in_accumulate_mode(self):
        pl = ProxyList()
        pl.setup(accumulate_updates=True)

        path = self.generate_plist_file('foo:1\nbar:1')
        pl.set_source('file', location=path)
        self.assertEqual(pl.get_next_proxy().server, 'foo')

        path = self.generate_plist_file('baz:1')
        pl.set_source('file', location=path)
        self.assertEqual(pl.get_next_proxy().server, 'bar')
        self.assertEqual(pl.get_next_proxy().server, 'baz')
        self.assertEqual(pl.get_next_proxy().server, 'foo')
