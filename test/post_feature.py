# coding: utf-8
from unittest import TestCase

from grab import Grab, GrabMisuseError
from util import FakeServerThread, BASE_URL, REQUEST, ignore_transport

class TestPostFeature(TestCase):
    def setUp(self):
        FakeServerThread().start()

    def test_post(self):
        g = Grab(url=BASE_URL, debug_post=True)

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

    @ignore_transport('GrabRequests')
    def test_multipart_post(self):
        g = Grab(url=BASE_URL, debug_post=True)
        
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
