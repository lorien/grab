# coding: utf-8
from unittest import TestCase
try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote

from grab import Grab, GrabMisuseError
from test.util import ignore_transport, build_grab
from test.server import SERVER
try:
    from urlparse import parse_qsl
except ImportError:
    from urllib.parse import parse_qsl

class TestPostFeature(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_post(self):
        g = build_grab(url=SERVER.BASE_URL, debug_post=True)

        # Provide POST data in dict
        g.setup(post={'foo': 'bar'})
        g.request()
        self.assertEqual(SERVER.REQUEST['post'], b'foo=bar')

        # Provide POST data in tuple
        g.setup(post=(('foo', 'TUPLE'),))
        g.request()
        self.assertEqual(SERVER.REQUEST['post'], b'foo=TUPLE')

        # Provide POST data in list
        g.setup(post=[('foo', 'LIST')])
        g.request()
        self.assertEqual(SERVER.REQUEST['post'], b'foo=LIST')

        # Order of elements should not be changed (1)
        g.setup(post=[('foo', 'LIST'), ('bar', 'BAR')])
        g.request()
        self.assertEqual(SERVER.REQUEST['post'], b'foo=LIST&bar=BAR')

        # Order of elements should not be changed (2)
        g.setup(post=[('bar', 'BAR'), ('foo', 'LIST')])
        g.request()
        self.assertEqual(SERVER.REQUEST['post'], b'bar=BAR&foo=LIST')

        # Provide POST data in byte-string
        g.setup(post='Hello world!')
        g.request()
        self.assertEqual(SERVER.REQUEST['post'], b'Hello world!')

        # Provide POST data in unicode-string
        g.setup(post=u'Hello world!')
        g.request()
        self.assertEqual(SERVER.REQUEST['post'], b'Hello world!')

        # Provide POST data in non-ascii unicode-string
        g.setup(post=u'Привет, мир!')
        g.request()
        self.assertEqual(SERVER.REQUEST['post'], u'Привет, мир!'.encode('utf-8'))

        # Two values with one key
        g.setup(post=(('foo', 'bar'), ('foo', 'baz')))
        g.request()
        self.assertEqual(SERVER.REQUEST['post'], b'foo=bar&foo=baz')

    def assertEqualQueryString(self, qs1, qs2):
        args1 = set([(x, y[0]) for x, y in parse_qsl(qs1)])
        args2 = set([(x, y[0]) for x, y in parse_qsl(qs2)])
        self.assertEqual(args1, args2)

    @ignore_transport('grab.transport.requests.RequestsTransport')
    @ignore_transport('grab.transport.kit.KitTransport')
    def test_multipart_post(self):
        g = build_grab(url=SERVER.BASE_URL, debug_post=True)
        
        # Dict
        g.setup(multipart_post={'foo': 'bar'})
        g.request()
        self.assertTrue(b'name="foo"' in SERVER.REQUEST['post'])

        # Few values with non-ascii data
        # TODO: understand and fix
        # AssertionError: 'foo=bar&gaz=%D0%94%D0%B5%D0%BB%D1%8C%D1%84%D0%B8%D0%BD&abc=' != 'foo=bar&gaz=\xd0\x94\xd0\xb5\xd0\xbb\xd1\x8c\xd1\x84\xd0\xb8\xd0\xbd&abc='
        #g.setup(post=({'foo': 'bar', 'gaz': u'Дельфин', 'abc': None}))
        #g.request()
        #self.assertEqual(SERVER.REQUEST['post'], 'foo=bar&gaz=Дельфин&abc=')

        # Multipart data could not be string
        g.setup(multipart_post='asdf')
        self.assertRaises(GrabMisuseError, lambda: g.request())

        # tuple with one pair
        g.setup(multipart_post=(('foo', 'bar'),))
        g.request()
        self.assertTrue(b'name="foo"' in SERVER.REQUEST['post'])

        # tuple with two pairs
        g.setup(multipart_post=(('foo', 'bar'), ('foo', 'baz')))
        g.request()
        self.assertTrue(b'name="foo"' in SERVER.REQUEST['post'])

    def test_unicode_post(self):
        # By default, unicode post should be converted into utf-8
        g = build_grab()
        data = u'фыва'
        g.setup(post=data, url=SERVER.BASE_URL)
        g.request()
        self.assertEqual(SERVER.REQUEST['post'], data.encode('utf-8'))

        # Now try cp1251 with charset option
        SERVER.REQUEST['charset'] = 'cp1251'
        g = build_grab()
        data = u'фыва'
        g.setup(post=data, url=SERVER.BASE_URL, charset='cp1251', debug=True)
        g.request()
        self.assertEqual(SERVER.REQUEST['post'], data.encode('cp1251'))

        # Now try dict with unicode value & charset option
        SERVER.REQUEST['charset'] = 'cp1251'
        g = build_grab()
        data = u'фыва'
        g.setup(post={'foo': data}, url=SERVER.BASE_URL, charset='cp1251', debug=True)
        g.request()
        test = 'foo=%s' % quote(data.encode('cp1251'))
        test = test.encode('utf-8') # py3 hack
        self.assertEqual(SERVER.REQUEST['post'], test)

    def test_put(self):
        g = build_grab()
        g.setup(post=b'abc', url=SERVER.BASE_URL, method='put', debug=True)
        SERVER.REQUEST['debug'] = True
        g.request()
        self.assertEqual(SERVER.REQUEST['method'], 'PUT')
        self.assertEqual(SERVER.REQUEST['headers']['content-length'], '3')

    def test_patch(self):
        g = build_grab()
        g.setup(post='abc', url=SERVER.BASE_URL, method='patch')
        g.request()
        self.assertEqual(SERVER.REQUEST['method'], 'PATCH')
        self.assertEqual(SERVER.REQUEST['headers']['content-length'], '3')
