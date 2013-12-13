# coding: utf-8
from unittest import TestCase
#import string
import json
import re

from grab import Grab, GrabMisuseError
from .util import TMP_FILE, GRAB_TRANSPORT, get_temp_file
from .tornado_util import SERVER

DEFAULT_PLIST_DATA = \
    '1.1.1.1:8080\n'\
    '1.1.1.2:8080\n'

class ProxyTestCase(TestCase):
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

    def test_file_load(self):
        g = Grab(transport=GRAB_TRANSPORT)
        path = self.generate_plist_file()
        g.proxylist.set_source('file', location=path)
        self.assertEqual(2, len(g.proxylist.proxy_list))

    def test_remote_load(self):
        g = Grab(transport=GRAB_TRANSPORT)
        SERVER.RESPONSE['get'] = DEFAULT_PLIST_DATA
        g.proxylist.set_source('url', url=SERVER.BASE_URL)
        self.assertEqual(2, len(g.proxylist.proxy_list))

    def test_accumulate_updates_basic(self):
        # test that all work with disabled accumulate_updates feature
        g = Grab(transport=GRAB_TRANSPORT)
        path = self.generate_plist_file()
        g.proxylist.setup(accumulate_updates=False)
        g.proxylist.set_source('file', location=path)
        self.assertEqual(2, len(g.proxylist.proxy_list))

        # enable accumulate updates
        g = Grab(transport=GRAB_TRANSPORT)
        path = self.generate_plist_file()
        g.proxylist.setup(accumulate_updates=True)
        g.proxylist.set_source('file', location=path)
        self.assertEqual(2, len(g.proxylist.proxy_list))

    def test_accumulate_updates_basic(self):
        g = Grab(transport=GRAB_TRANSPORT)
        g.proxylist.setup(accumulate_updates=True)

        # load initial list
        path = self.generate_plist_file('foo:1\nbar:1')
        g.proxylist.set_source('file', location=path)
        self.assertEqual(2, len(g.proxylist.proxy_list))

        # load list with one new and one old proxies
        with open(path, 'w') as out:
            out.write('foo:1\nbaz:1')
        g.proxylist.reload(force=True)
        self.assertEqual(3, len(g.proxylist.proxy_list))

    def test_get_next_proxy(self):
        g = Grab(transport=GRAB_TRANSPORT)
        path = self.generate_plist_file('foo:1\nbar:1')
        g.proxylist.set_source('file', location=path)
        self.assertEqual(g.proxylist.get_next_proxy().server, 'foo')
        self.assertEqual(g.proxylist.get_next_proxy().server, 'bar')
        self.assertEqual(g.proxylist.get_next_proxy().server, 'foo')
        g.proxylist.set_source('file', location=path)
        self.assertEqual(g.proxylist.get_next_proxy().server, 'foo')

    def test_get_next_proxy_in_accumulate_mode(self):
        g = Grab(transport=GRAB_TRANSPORT)
        g.proxylist.setup(accumulate_updates=True)

        path = self.generate_plist_file('foo:1\nbar:1')
        g.proxylist.set_source('file', location=path)
        self.assertEqual(g.proxylist.get_next_proxy().server, 'foo')

        path = self.generate_plist_file('baz:1')
        g.proxylist.set_source('file', location=path)
        self.assertEqual(g.proxylist.get_next_proxy().server, 'bar')
        self.assertEqual(g.proxylist.get_next_proxy().server, 'baz')
        self.assertEqual(g.proxylist.get_next_proxy().server, 'foo')
