from pprint import pprint  # pylint: disable=unused-import

from test_server import Response

from grab import request
from tests.util import BaseTestCase


class TestPostFeature(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    def test_post(self) -> None:
        self.server.add_response(Response(), count=9)

        # Provide POST data in dict
        request(
            url=self.server.get_url(),
            fields={"foo": "bar"},
            method="POST",
            multipart=False,
        )
        self.assertEqual(self.server.request.data, b"foo=bar")

        # Provide POST data in tuple
        request(
            url=self.server.get_url(),
            fields=(("foo", "TUPLE"),),
            method="POST",
            multipart=False,
        )
        self.assertEqual(self.server.request.data, b"foo=TUPLE")

        # Provide POST data in list
        request(
            url=self.server.get_url(),
            fields=[("foo", "LIST")],
            method="POST",
            multipart=False,
        )
        self.assertEqual(self.server.request.data, b"foo=LIST")

        # Order of elements should not be changed (1)
        request(
            url=self.server.get_url(),
            fields=[("foo", "LIST"), ("bar", "BAR")],
            method="POST",
            multipart=False,
        )
        self.assertEqual(self.server.request.data, b"foo=LIST&bar=BAR")

        # Order of elements should not be changed (2)
        request(
            url=self.server.get_url(),
            fields=[("bar", "BAR"), ("foo", "LIST")],
            method="POST",
            multipart=False,
        )
        self.assertEqual(self.server.request.data, b"bar=BAR&foo=LIST")

        # Provide POST data in byte-string
        request(
            url=self.server.get_url(),
            body="Hello world!",
            method="POST",
            multipart=False,
        )
        self.assertEqual(self.server.request.data, b"Hello world!")

        # Provide POST data in unicode-string
        request(
            url=self.server.get_url(),
            body="Hello world!",
            method="POST",
            multipart=False,
        )
        self.assertEqual(self.server.request.data, b"Hello world!")

        # Provide POST data in non-ascii unicode-string
        # request(body="Привет, мир!", method="POST", multipart=False)
        # self.assertEqual(self.server.request.data, "Привет, мир!".encode("utf-8"))

        # Two values with one key
        request(
            url=self.server.get_url(),
            fields=[("foo", "bar"), ("foo", "baz")],
            method="POST",
            multipart=False,
        )
        self.assertEqual(self.server.request.data, b"foo=bar&foo=baz")

    def test_multipart_post(self) -> None:
        self.server.add_response(Response(), count=3)
        # Dict
        request(
            url=self.server.get_url(),
            multipart=True,
            method="POST",
            fields={"foo": "bar"},
        )
        self.assertTrue(b'name="foo"' in self.server.request.data)

        # tuple with one pair
        request(
            method="POST",
            url=self.server.get_url(),
            multipart=True,
            fields=(("foo", "bar"),),
        )
        self.assertTrue(b'name="foo"' in self.server.request.data)

        # tuple with two pairs
        request(
            url=self.server.get_url(),
            multipart=True,
            fields=(("foo", "bar"), ("foo", "baz")),
            method="POST",
        )
        self.assertTrue(b'name="foo"' in self.server.request.data)

    # def test_unicode_post(self):
    #    self.server.add_response(Response(), count=3)
    #    # By default, unicode post should be converted into utf-8
    #    data = "фыва"
    #    grab.setup(body=data, url=self.server.get_url())
    #    request()
    #    self.assertEqual(self.server.request.data, data.encode("utf-8"))

    #    # Now try cp1251 with encoding option
    #    data = "фыва"
    #    grab.setup(body=data, url=self.server.get_url(), encoding="cp1251")
    #    request()
    #    self.assertEqual(self.server.request.data, data.encode("cp1251"))

    #    # Now try dict with unicode value & encoding option
    #    data = "фыва"
    #    grab.setup(fields={"foo": data}, url=self.server.get_url(), encoding="cp1251")
    #    request()
    #    test = ("foo=%s" % quote(data.encode("cp1251"))).encode("ascii")
    #    self.assertEqual(self.server.request.data, test)

    def test_put(self) -> None:
        self.server.add_response(Response())
        request(body=b"abc", url=self.server.get_url(), method="PUT")
        self.assertEqual(self.server.request.method, "PUT")
        self.assertEqual(self.server.request.headers.get("content-length"), "3")

    def test_patch(self) -> None:
        self.server.add_response(Response())
        request(body=b"abc", url=self.server.get_url(), method="PATCH")
        self.assertEqual(self.server.request.method, "PATCH")
        self.assertEqual(self.server.request.headers.get("content-length"), "3")

    def test_empty_post(self) -> None:
        self.server.add_response(Response(), count=2)
        request(self.server.get_url(), method="POST", body="")
        self.assertEqual(self.server.request.method, "POST")
        self.assertEqual(self.server.request.data, b"")
        self.assertEqual(self.server.request.headers.get("content-length"), "0")

        request(self.server.get_url(), body="DATA", method="POST")
        self.assertEqual(self.server.request.headers.get("content-length"), "4")
