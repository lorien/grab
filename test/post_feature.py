# coding: utf-8
from unittest import TestCase
import urllib

from grab import Grab, GrabMisuseError
from util import (FakeServerThread, BASE_URL, REQUEST, ignore_transport,
                  GRAB_TRANSPORT)
from urlparse import parse_qsl

class TestPostFeature(TestCase):
    def setUp(self):
        FakeServerThread().start()

    def test_post(self):
        g = Grab(url=BASE_URL, debug_post=True, transport=GRAB_TRANSPORT)

        # Provide POST data in dict
        g.setup(post={'foo': 'bar'})
        g.request()
        self.assertEqual(REQUEST['post'], 'foo=bar')

        # Provide POST data in tuple
        g.setup(post=(('foo', 'TUPLE'),))
        g.request()
        self.assertEqual(REQUEST['post'], 'foo=TUPLE')

        # Provide POST data in list
        g.setup(post=[('foo', 'LIST')])
        g.request()
        self.assertEqual(REQUEST['post'], 'foo=LIST')

        # Order of elements should not be changed (1)
        g.setup(post=[('foo', 'LIST'), ('bar', 'BAR')])
        g.request()
        self.assertEqual(REQUEST['post'], 'foo=LIST&bar=BAR')

        # Order of elements should not be changed (2)
        g.setup(post=[('bar', 'BAR'), ('foo', 'LIST')])
        g.request()
        self.assertEqual(REQUEST['post'], 'bar=BAR&foo=LIST')

        # Provide POST data in byte-string
        g.setup(post='Hello world!')
        g.request()
        self.assertEqual(REQUEST['post'], 'Hello world!')

        # Provide POST data in unicode-string
        g.setup(post=u'Hello world!')
        g.request()
        self.assertEqual(REQUEST['post'], 'Hello world!')

        # Provide POST data in non-ascii unicode-string
        g.setup(post=u'Привет, мир!')
        g.request()
        self.assertEqual(REQUEST['post'], 'Привет, мир!')

        # Two values with one key
        g.setup(post=(('foo', 'bar'), ('foo', 'baz')))
        g.request()
        self.assertEqual(REQUEST['post'], 'foo=bar&foo=baz')

    def assertEqualQueryString(self, qs1, qs2):
        args1 = set([(x, y[0]) for x, y in parse_qsl(qs1)])
        args2 = set([(x, y[0]) for x, y in parse_qsl(qs2)])
        self.assertEqual(args1, args2)

    @ignore_transport('requests.RequestsTransport')
    def test_multipart_post(self):
        g = Grab(url=BASE_URL, debug_post=True, transport=GRAB_TRANSPORT)
        
        # Dict
        g.setup(multipart_post={'foo': 'bar'})
        g.request()
        self.assertTrue('name="foo"' in REQUEST['post'])

        # Few values with non-ascii data
        # TODO: understand and fix
        # AssertionError: 'foo=bar&gaz=%D0%94%D0%B5%D0%BB%D1%8C%D1%84%D0%B8%D0%BD&abc=' != 'foo=bar&gaz=\xd0\x94\xd0\xb5\xd0\xbb\xd1\x8c\xd1\x84\xd0\xb8\xd0\xbd&abc='
        #g.setup(post=({'foo': 'bar', 'gaz': u'Дельфин', 'abc': None}))
        #g.request()
        #self.assertEqual(REQUEST['post'], 'foo=bar&gaz=Дельфин&abc=')

        # Multipart data could not be string
        g.setup(multipart_post='asdf')
        self.assertRaises(GrabMisuseError, lambda: g.request())

        # tuple with one pair
        g.setup(multipart_post=(('foo', 'bar'),))
        g.request()
        self.assertTrue('name="foo"' in REQUEST['post'])

        # tuple with two pairs
        g.setup(multipart_post=(('foo', 'bar'), ('foo', 'baz')))
        g.request()
        self.assertTrue('name="foo"' in REQUEST['post'])

    def test_unicode_post(self):
        # By default, unicode post shuuld be converted into utf-8
        g = Grab()
        data = u'фыва'
        g.setup(post=data, url=BASE_URL)
        g.request()
        self.assertEqual(REQUEST['post'], data.encode('utf-8'))

        # Now try cp1251 with charset option
        g = Grab()
        data = u'фыва'
        g.setup(post=data, url=BASE_URL, charset='cp1251')
        g.request()
        self.assertEqual(REQUEST['post'], data.encode('cp1251'))

        # Now try dict with unicode value & charset option
        g = Grab()
        data = u'фыва'
        g.setup(post={'foo': data}, url=BASE_URL, charset='cp1251')
        g.request()
        self.assertEqual(REQUEST['post'], 'foo=%s' % urllib.quote(data.encode('cp1251')))
