from test_server import Response

from grab import Grab, request
from tests.util import BaseTestCase  # , temp_file


class TestCookies(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    def test_parsing_response_cookies(self) -> None:
        self.server.add_response(
            Response(headers=[("Set-Cookie", "foo=bar"), ("Set-Cookie", "1=2")])
        )
        doc = request(self.server.get_url())
        self.assertTrue(any(x.name == "foo" and x.value == "bar" for x in doc.cookies))

    def test_multiple_cookies(self) -> None:
        self.server.add_response(Response())
        request(self.server.get_url(), client=Grab, cookies={"foo": "1", "bar": "2"})
        self.assertEqual(
            {(x.key, x.value) for x in self.server.request.cookies.values()},
            {("foo", "1"), ("bar", "2")},
        )

    def test_session(self) -> None:
        # Test that if Grab gets some cookies from the server
        # then it sends it back

        grab = Grab()
        self.server.add_response(Response(headers=[("Set-Cookie", "foo=bar")]))
        doc = grab.request(self.server.get_url())
        self.assertTrue(any(x.name == "foo" and x.value == "bar" for x in doc.cookies))
        self.server.add_response(Response())
        grab.request(self.server.get_url())
        self.assertEqual(
            {("foo", "bar")},
            {(x.key, x.value) for x in self.server.request.cookies.values()},
        )
        self.server.add_response(Response())
        grab.request(self.server.get_url())
        self.assertEqual(
            {("foo", "bar")},
            {(x.key, x.value) for x in self.server.request.cookies.values()},
        )

        # # Test reuse_cookies=False
        # grab = Grab(reuse_cookies=False)
        # self.server.add_response(Response(headers=[("Set-Cookie", "foo=bar")]))
        # doc = grab.request(self.server.get_url())
        # self.assertTrue(
        # any(x.name == "foo" and x.value == "bar" for x in doc.cookies))
        # self.server.add_response(Response())
        # grab.request(self.server.get_url())
        # self.assertFalse(self.server.request.cookies)

        # Test something
        grab = Grab()
        self.server.add_response(Response(headers=[("Set-Cookie", "foo=bar")]))
        doc = grab.request(self.server.get_url())
        self.assertTrue(any(x.name == "foo" and x.value == "bar" for x in doc.cookies))
        grab.cookies.clear()
        self.server.add_response(Response())
        grab.request(self.server.get_url())
        self.assertFalse(self.server.request.cookies)

    def test_redirect_session(self) -> None:
        self.server.add_response(Response(headers=[("Set-Cookie", "foo=bar")]))
        grab = Grab()
        doc = grab.request(self.server.get_url())
        self.assertTrue(any(x.name == "foo" and x.value == "bar" for x in doc.cookies))

        # Setup one-time redirect
        self.server.add_response(
            Response(
                headers=[
                    ("Location", self.server.get_url()),
                    ("Set-Cookie", "foo=bar"),
                ],
                status=302,
            )
        )
        self.server.add_response(Response())
        grab.request(self.server.get_url())
        self.assertTrue(
            any(x.name == "foo" and x.value == "bar" for x in grab.cookies.cookiejar)
        )

    # def test_load_dump(self):
    #    with temp_file() as tmp_file:
    #        self.server.add_response(Response())
    #        cookies = {"foo": "bar", "spam": "ham"}
    #        grab.setup(cookies=cookies)
    #        request(self.server.get_url())
    #        grab.cookies.save_to_file(tmp_file)
    #        with open(tmp_file, encoding="utf-8") as inp:
    #            self.assertEqual(
    #                set(cookies.items()),
    #                {(x["name"], x["value"]) for x in json.load(inp)},
    #            )

    #        self.server.add_response(Response())
    #        cookies = {"foo": "bar", "spam": "begemot"}
    #        grab.setup(cookies=cookies)
    #        request(self.server.get_url())
    #        grab.cookies.save_to_file(tmp_file)
    #        with open(tmp_file, encoding="utf-8") as inp:
    #            self.assertEqual(
    #                set(cookies.items()),
    #                {(x["name"], x["value"]) for x in json.load(inp)},
    #            )

    #        # Test load cookies
    #        cookies_list = [
    #            {"name": "foo", "value": "bar", "domain": self.server.address},
    #            {"name": "spam", "value": "begemot", "domain": self.server.address},
    #        ]
    #        with open(tmp_file, "w", encoding="utf-8") as out:
    #            json.dump(cookies_list, out)
    #        grab.cookies.load_from_file(tmp_file)
    #        self.assertEqual(
    #            set(grab.cookies.items()),
    #            {(x["name"], x["value"]) for x in cookies_list},
    #        )

    # def test_update_invalid_cookie(self):
    #    self.assertRaises(GrabMisuseError, grab.cookies.update, None)
    #    self.assertRaises(GrabMisuseError, grab.cookies.update, "asdf")
    #    self.assertRaises(GrabMisuseError, grab.cookies.update, ["asdf"])

    def test_path(self) -> None:
        grab = Grab()
        self.server.add_response(
            Response(
                headers=[
                    ("Set-Cookie", "foo=1; path=/;"),
                    ("Set-Cookie", "bar=1; path=/admin;"),
                ]
            )
        )

        # work with "/" path
        # get cookies
        grab.request(self.server.get_url("/"))

        self.server.add_response(Response())
        # submit received cookies
        grab.request(self.server.get_url("/"))
        self.assertEqual(1, len(self.server.request.cookies))

        self.server.add_response(Response())
        # work with "/admin" path
        grab.request(self.server.get_url("/admin/zz"))
        self.assertEqual(2, len(self.server.request.cookies))

    # def test_cookie_merging_replace_with_cookies_option(self):
    #    with temp_file() as tmp_file:
    #        self.server.add_response(Response())
    #        init_cookies = [
    #            {"name": "foo", "value": "bar", "domain": self.server.address}
    #        ]
    #        with open(tmp_file, "w", encoding="utf-8") as out:
    #            json.dump(init_cookies, out)

    #        grab.cookies.load_from_file(tmp_file)

    #        cookies = {
    #            "foo": "bar2",
    #            "sex": "male",
    #        }

    #        grab.setup(cookies=cookies)
    #        request(self.server.get_url())
    #        self.assertEqual(2, len(self.server.get_request().cookies))

    # def test_cookie_merging_replace(self):
    #    grab.cookies.set("foo", "bar", "localhost")
    #    grab.cookies.set("foo", "bar2", "localhost")
    #    self.assertEqual(1, len(grab.cookies.items()))

    #    # Empty domain as same as localhost because internally
    #    # localhost replaced with empty string
    #    grab.cookies.set("foo", "bar3", "")
    #    self.assertEqual(1, len(grab.cookies.items()))

    #    grab.cookies.set("foo", "bar2", domain="ya.ru")
    #    self.assertEqual(2, len(grab.cookies.items()))

    def test_unicode_cookie(self) -> None:
        def callback() -> bytes:
            return b"HTTP/1.0 200 OK\nSet-Cookie: preved=%s\n\n" % "медвед".encode(
                "utf-8"
            )

        self.server.add_response(Response(raw_callback=callback))
        self.server.add_response(Response())
        # request page and receive unicode cookie
        request(self.server.get_url())
        # request page one more time, sending cookie
        # should not fail
        request(self.server.get_url())

    def test_different_instances(self) -> None:
        grab1 = Grab()
        self.server.add_response(Response(headers=[("Set-Cookie", "key1=val1")]))
        doc1 = grab1.request(self.server.get_url())
        self.assertTrue(
            all(x.name == "key1" and x.value == "val1" for x in doc1.cookies)
        )
        self.assertTrue(
            all(x.name == "key1" and x.value == "val1" for x in grab1.cookies.cookiejar)
        )

        grab2 = Grab()
        self.server.add_response(Response(headers=[("Set-Cookie", "key2=val2")]))
        doc2 = grab2.request(self.server.get_url())
        self.assertTrue(
            all(x.name == "key2" and x.value == "val2" for x in doc2.cookies)
        )
        self.assertTrue(
            all(x.name == "key2" and x.value == "val2" for x in grab2.cookies.cookiejar)
        )

        # double check grab1
        self.assertTrue(
            all(x.name == "key1" and x.value == "val1" for x in doc1.cookies)
        )
        self.assertTrue(
            all(x.name == "key1" and x.value == "val1" for x in grab1.cookies.cookiejar)
        )
