# coding: utf-8
try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote

from grab import GrabMisuseError
from test_server import Request, Response
from tests.util import BaseGrabTestCase, build_grab


class TestPostFeature(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_post(self):
        grab = build_grab(url=self.server.get_url(), debug_post=True)

        # Provide POST data in dict
        grab.setup(post={"foo": "bar"})
        self.server.add_response(Response())
        grab.request()
        req = self.server.get_request()
        self.assertEqual(req.data, b"foo=bar")

        # Provide POST data in tuple
        grab.setup(post=(("foo", "TUPLE"),))
        self.server.add_response(Response())
        grab.request()
        req = self.server.get_request()
        self.assertEqual(req.data, b"foo=TUPLE")

        # Provide POST data in list
        grab.setup(post=[("foo", "LIST")])
        self.server.add_response(Response())
        grab.request()
        req = self.server.get_request()
        self.assertEqual(req.data, b"foo=LIST")

        # Order of elements should not be changed (1)
        grab.setup(post=[("foo", "LIST"), ("bar", "BAR")])
        self.server.add_response(Response())
        grab.request()
        req = self.server.get_request()
        self.assertEqual(req.data, b"foo=LIST&bar=BAR")

        # Order of elements should not be changed (2)
        grab.setup(post=[("bar", "BAR"), ("foo", "LIST")])
        self.server.add_response(Response())
        grab.request()
        req = self.server.get_request()
        self.assertEqual(req.data, b"bar=BAR&foo=LIST")

        # Provide POST data in byte-string
        grab.setup(post="Hello world!")
        self.server.add_response(Response())
        grab.request()
        req = self.server.get_request()
        self.assertEqual(req.data, b"Hello world!")

        # Provide POST data in unicode-string
        grab.setup(post="Hello world!")
        self.server.add_response(Response())
        grab.request()
        req = self.server.get_request()
        self.assertEqual(req.data, b"Hello world!")

        # Provide POST data in non-ascii unicode-string
        grab.setup(post="Привет, мир!")
        self.server.add_response(Response())
        grab.request()
        req = self.server.get_request()
        # fmt: off
        self.assertEqual(req.data, u"Привет, мир!".encode("utf-8"))
        # fmt: on

        # Two values with one key
        grab.setup(post=(("foo", "bar"), ("foo", "baz")))
        self.server.add_response(Response())
        grab.request()
        req = self.server.get_request()
        self.assertEqual(req.data, b"foo=bar&foo=baz")

    def test_multipart_post(self):
        grab = build_grab(url=self.server.get_url(), debug_post=True)
        # Dict
        grab.setup(multipart_post={"foo": "bar"})
        self.server.add_response(Response())
        grab.request()
        req = self.server.get_request()
        self.assertTrue(b'name="foo"' in req.data)

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
        grab.setup(multipart_post=(("foo", "bar"),))
        self.server.add_response(Response())
        grab.request()
        req = self.server.get_request()
        self.assertTrue(b'name="foo"' in req.data)

        # tuple with two pairs
        grab.setup(multipart_post=(("foo", "bar"), ("foo", "baz")))
        self.server.add_response(Response())
        grab.request()
        req = self.server.get_request()
        self.assertTrue(b'name="foo"' in req.data)

    def test_unicode_post(self):
        # By default, unicode post should be converted into utf-8
        grab = build_grab()
        # fmt: off
        data = u"фыва"
        # fmt: on
        grab.setup(post=data, url=self.server.get_url())
        self.server.add_response(Response())
        grab.request()
        req = self.server.get_request()
        self.assertEqual(req.data, data.encode("utf-8"))

        # Now try cp1251 with charset option
        # self.server.request["charset"] = "cp1251"
        grab = build_grab()
        # fmt: off
        data = u"фыва"
        # fmt: on
        grab.setup(post=data, url=self.server.get_url(), charset="cp1251", debug=True)
        self.server.add_response(Response())
        grab.request()
        req = self.server.get_request()
        self.assertEqual(req.data, data.encode("cp1251"))

        # Now try dict with unicode value & charset option
        # self.server.request["charset"] = "cp1251"
        grab = build_grab()
        # fmt: off
        data = u"фыва"
        # fmt: on
        grab.setup(
            post={"foo": data}, url=self.server.get_url(), charset="cp1251", debug=True
        )
        self.server.add_response(Response())
        grab.request()
        test = "foo=%s" % quote(data.encode("cp1251"))
        test = test.encode("utf-8")  # py3 hack
        req = self.server.get_request()
        self.assertEqual(req.data, test)

    def test_put(self):
        grab = build_grab()
        grab.setup(post=b"abc", url=self.server.get_url(), method="put", debug=True)
        # self.server.request["debug"] = True
        self.server.add_response(Response())
        grab.request()
        req = self.server.get_request()
        self.assertEqual(req.method, "PUT")
        req = self.server.get_request()
        self.assertEqual(req.headers.get("content-length"), "3")

    def test_patch(self):
        grab = build_grab()
        grab.setup(post=b"abc", url=self.server.get_url(), method="patch")
        self.server.add_response(Response())
        grab.request()
        req = self.server.get_request()
        self.assertEqual(req.method, "PATCH")
        req = self.server.get_request()
        self.assertEqual(req.headers.get("content-length"), "3")

    def test_empty_post(self):
        grab = build_grab()
        grab.setup(method="post", post="")

        self.server.add_response(Response())
        grab.go(self.server.get_url())
        req = self.server.get_request()
        self.assertEqual(req.method, "POST")
        req = self.server.get_request()
        self.assertEqual(req.data, b"")
        req = self.server.get_request()
        self.assertEqual(req.headers.get("content-length"), "0")

        self.server.add_response(Response())
        grab.go(self.server.get_url(), post="DATA")
        req = self.server.get_request()
        self.assertEqual(req.headers.get("content-length"), "4")

    def test_method_post_nobody(self):
        grab = build_grab()
        grab.setup(method="post")
        self.server.add_response(Response())
        self.assertRaises(GrabMisuseError, grab.go, self.server.get_url())

    def test_post_multivalue_key(self):
        grab = build_grab()
        grab.setup(post=[("foo", [1, 2])])
        self.server.add_response(Response())
        grab.go(self.server.get_url())
        self.assertEqual(self.server.get_request().data, b"foo=1&foo=2")
