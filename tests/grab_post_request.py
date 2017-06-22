# coding: utf-8
try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote

from tests.util import build_grab
from tests.util import BaseGrabTestCase
from grab import GrabMisuseError


class TestPostFeature(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_post(self):
        grab = build_grab(url=self.server.get_url(), debug_post=True)

        # Provide POST data in dict
        grab.setup(post={'foo': 'bar'})
        grab.request()
        self.assertEqual(self.server.request['data'], b'foo=bar')

        # Provide POST data in tuple
        grab.setup(post=(('foo', 'TUPLE'),))
        grab.request()
        self.assertEqual(self.server.request['data'], b'foo=TUPLE')

        # Provide POST data in list
        grab.setup(post=[('foo', 'LIST')])
        grab.request()
        self.assertEqual(self.server.request['data'], b'foo=LIST')

        # Order of elements should not be changed (1)
        grab.setup(post=[('foo', 'LIST'), ('bar', 'BAR')])
        grab.request()
        self.assertEqual(self.server.request['data'], b'foo=LIST&bar=BAR')

        # Order of elements should not be changed (2)
        grab.setup(post=[('bar', 'BAR'), ('foo', 'LIST')])
        grab.request()
        self.assertEqual(self.server.request['data'], b'bar=BAR&foo=LIST')

        # Provide POST data in byte-string
        grab.setup(post='Hello world!')
        grab.request()
        self.assertEqual(self.server.request['data'], b'Hello world!')

        # Provide POST data in unicode-string
        grab.setup(post=u'Hello world!')
        grab.request()
        self.assertEqual(self.server.request['data'], b'Hello world!')

        # Provide POST data in non-ascii unicode-string
        grab.setup(post=u'Привет, мир!')
        grab.request()
        self.assertEqual(self.server.request['data'],
                         u'Привет, мир!'.encode('utf-8'))

        # Two values with one key
        grab.setup(post=(('foo', 'bar'), ('foo', 'baz')))
        grab.request()
        self.assertEqual(self.server.request['data'], b'foo=bar&foo=baz')

    def test_multipart_post(self):
        grab = build_grab(url=self.server.get_url(), debug_post=True)
        # Dict
        grab.setup(multipart_post={'foo': 'bar'})
        grab.request()
        self.assertTrue(b'name="foo"' in self.server.request['data'])

        # Few values with non-ascii data
        # TODO: understand and fix
        # AssertionError: 'foo=bar&gaz=%D0%94%D0%B5%D0%BB%'\
        #                 'D1%8C%D1%84%D0%B8%D0%BD&abc=' !=
        #                 'foo=bar&gaz=\xd0\x94\xd0\xb5\xd0'\
        #                 '\xbb\xd1\x8c\xd1\x84\xd0\xb8\xd0\xbd&abc='
        # grab.setup(post=({'foo': 'bar', 'gaz': u'Дельфин', 'abc': None}))
        # grab.request()
        # self.assertEqual(self.server.request['data'],
        #                   'foo=bar&gaz=Дельфин&abc=')

        # tuple with one pair
        grab.setup(multipart_post=(('foo', 'bar'),))
        grab.request()
        self.assertTrue(b'name="foo"' in self.server.request['data'])

        # tuple with two pairs
        grab.setup(multipart_post=(('foo', 'bar'), ('foo', 'baz')))
        grab.request()
        self.assertTrue(b'name="foo"' in self.server.request['data'])

    def test_unicode_post(self):
        # By default, unicode post should be converted into utf-8
        grab = build_grab()
        data = u'фыва'
        grab.setup(post=data, url=self.server.get_url())
        grab.request()
        self.assertEqual(self.server.request['data'], data.encode('utf-8'))

        # Now try cp1251 with charset option
        self.server.request['charset'] = 'cp1251'
        grab = build_grab()
        data = u'фыва'
        grab.setup(post=data, url=self.server.get_url(),
                   charset='cp1251', debug=True)
        grab.request()
        self.assertEqual(self.server.request['data'], data.encode('cp1251'))

        # Now try dict with unicode value & charset option
        self.server.request['charset'] = 'cp1251'
        grab = build_grab()
        data = u'фыва'
        grab.setup(post={'foo': data}, url=self.server.get_url(),
                   charset='cp1251', debug=True)
        grab.request()
        test = 'foo=%s' % quote(data.encode('cp1251'))
        test = test.encode('utf-8')  # py3 hack
        self.assertEqual(self.server.request['data'], test)

    def test_put(self):
        grab = build_grab()
        grab.setup(post=b'abc', url=self.server.get_url(),
                   method='put', debug=True)
        self.server.request['debug'] = True
        grab.request()
        self.assertEqual(self.server.request['method'], 'PUT')
        self.assertEqual(self.server.request['headers']['content-length'], '3')

    def test_patch(self):
        grab = build_grab()
        grab.setup(post=b'abc', url=self.server.get_url(), method='patch')
        grab.request()
        self.assertEqual(self.server.request['method'], 'PATCH')
        self.assertEqual(self.server.request['headers']['content-length'], '3')

    def test_empty_post(self):
        grab = build_grab()
        grab.setup(method='post', post='')
        grab.go(self.server.get_url())
        self.assertEqual(self.server.request['method'], 'POST')
        self.assertEqual(self.server.request['data'], b'')
        self.assertEqual(self.server.request['headers']['content-length'], '0')

        grab.go(self.server.get_url(), post='DATA')
        self.assertEqual(self.server.request['headers']['content-length'], '4')

    def test_method_post_nobody(self):
        grab = build_grab()
        grab.setup(method='post')
        self.assertRaises(GrabMisuseError, grab.go, self.server.get_url())
