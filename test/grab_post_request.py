# coding: utf-8
try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote

from grab import GrabMisuseError
from test.util import build_grab
from test.util import BaseGrabTestCase
try:
    from urlparse import parse_qsl
except ImportError:
    from urllib.parse import parse_qsl


class TestPostFeature(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_post(self):
        g = build_grab(url=self.server.get_url(), debug_post=True)

        # Provide POST data in dict
        g.setup(post={'foo': 'bar'})
        g.request()
        self.assertEqual(self.server.request['data'], b'foo=bar')

        # Provide POST data in tuple
        g.setup(post=(('foo', 'TUPLE'),))
        g.request()
        self.assertEqual(self.server.request['data'], b'foo=TUPLE')

        # Provide POST data in list
        g.setup(post=[('foo', 'LIST')])
        g.request()
        self.assertEqual(self.server.request['data'], b'foo=LIST')

        # Order of elements should not be changed (1)
        g.setup(post=[('foo', 'LIST'), ('bar', 'BAR')])
        g.request()
        self.assertEqual(self.server.request['data'], b'foo=LIST&bar=BAR')

        # Order of elements should not be changed (2)
        g.setup(post=[('bar', 'BAR'), ('foo', 'LIST')])
        g.request()
        self.assertEqual(self.server.request['data'], b'bar=BAR&foo=LIST')

        # Provide POST data in byte-string
        g.setup(post='Hello world!')
        g.request()
        self.assertEqual(self.server.request['data'], b'Hello world!')

        # Provide POST data in unicode-string
        g.setup(post=u'Hello world!')
        g.request()
        self.assertEqual(self.server.request['data'], b'Hello world!')

        # Provide POST data in non-ascii unicode-string
        g.setup(post=u'Привет, мир!')
        g.request()
        self.assertEqual(self.server.request['data'],
                         u'Привет, мир!'.encode('utf-8'))

        # Two values with one key
        g.setup(post=(('foo', 'bar'), ('foo', 'baz')))
        g.request()
        self.assertEqual(self.server.request['data'], b'foo=bar&foo=baz')

    def assertEqualQueryString(self, qs1, qs2):
        args1 = set([(x, y[0]) for x, y in parse_qsl(qs1)])
        args2 = set([(x, y[0]) for x, y in parse_qsl(qs2)])
        self.assertEqual(args1, args2)

    def test_multipart_post(self):
        g = build_grab(url=self.server.get_url(), debug_post=True)
        # Dict
        g.setup(multipart_post={'foo': 'bar'})
        g.request()
        self.assertTrue(b'name="foo"' in self.server.request['data'])

        # Few values with non-ascii data
        # TODO: understand and fix
        # AssertionError: 'foo=bar&gaz=%D0%94%D0%B5%D0%BB%'\
        #                 'D1%8C%D1%84%D0%B8%D0%BD&abc=' !=
        #                 'foo=bar&gaz=\xd0\x94\xd0\xb5\xd0'\
        #                 '\xbb\xd1\x8c\xd1\x84\xd0\xb8\xd0\xbd&abc='
        # g.setup(post=({'foo': 'bar', 'gaz': u'Дельфин', 'abc': None}))
        # g.request()
        # self.assertEqual(self.server.request['data'],
        #                   'foo=bar&gaz=Дельфин&abc=')

        # Multipart data could not be string
        g.setup(multipart_post='asdf')
        self.assertRaises(GrabMisuseError, lambda: g.request())

        # tuple with one pair
        g.setup(multipart_post=(('foo', 'bar'),))
        g.request()
        self.assertTrue(b'name="foo"' in self.server.request['data'])

        # tuple with two pairs
        g.setup(multipart_post=(('foo', 'bar'), ('foo', 'baz')))
        g.request()
        self.assertTrue(b'name="foo"' in self.server.request['data'])

    def test_unicode_post(self):
        # By default, unicode post should be converted into utf-8
        g = build_grab()
        data = u'фыва'
        g.setup(post=data, url=self.server.get_url())
        g.request()
        self.assertEqual(self.server.request['data'], data.encode('utf-8'))

        # Now try cp1251 with charset option
        self.server.request['charset'] = 'cp1251'
        g = build_grab()
        data = u'фыва'
        g.setup(post=data, url=self.server.get_url(),
                charset='cp1251', debug=True)
        g.request()
        self.assertEqual(self.server.request['data'], data.encode('cp1251'))

        # Now try dict with unicode value & charset option
        self.server.request['charset'] = 'cp1251'
        g = build_grab()
        data = u'фыва'
        g.setup(post={'foo': data}, url=self.server.get_url(),
                charset='cp1251', debug=True)
        g.request()
        test = 'foo=%s' % quote(data.encode('cp1251'))
        test = test.encode('utf-8')  # py3 hack
        self.assertEqual(self.server.request['data'], test)

    def test_put(self):
        g = build_grab()
        g.setup(post=b'abc', url=self.server.get_url(),
                method='put', debug=True)
        self.server.request['debug'] = True
        g.request()
        self.assertEqual(self.server.request['method'], 'PUT')
        self.assertEqual(self.server.request['headers']['content-length'], '3')

    def test_patch(self):
        g = build_grab()
        g.setup(post=b'abc', url=self.server.get_url(), method='patch')
        g.request()
        self.assertEqual(self.server.request['method'], 'PATCH')
        self.assertEqual(self.server.request['headers']['content-length'], '3')

    def test_empty_post(self):
        g = build_grab()
        g.setup(method='post')
        g.go(self.server.get_url())
        self.assertEqual(self.server.request['method'], 'POST')
        self.assertEqual(self.server.request['data'], b'')
        self.assertEqual(self.server.request['headers']['content-length'], '0')

        g.go(self.server.get_url(), post='DATA')
        self.assertEqual(self.server.request['headers']['content-length'], '4')
