from pprint import pprint  # pylint: disable=unused-import

from test_server import Response

from tests.util import BaseGrabTestCase, build_grab  # , temp_file


class TestCookies(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_parsing_response_cookies(self):
        grab = build_grab()
        self.server.add_response(
            Response(headers=[("Set-Cookie", "foo=bar"), ("Set-Cookie", "1=2")])
        )
        doc = grab.request(self.server.get_url())
        self.assertTrue(any(x.name == "foo" and x.value == "bar" for x in doc.cookies))

    def test_multiple_cookies(self):
        grab = build_grab()
        self.server.add_response(Response())
        grab.request(self.server.get_url(), cookies={"foo": "1", "bar": "2"})
        self.assertEqual(
            {(x.key, x.value) for x in self.server.request.cookies.values()},
            {("foo", "1"), ("bar", "2")},
        )

    def test_session(self):
        # Test that if Grab gets some cookies from the server
        # then it sends it back
        grab = build_grab()
        grab.setup(reuse_cookies=True)
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

        # Test reuse_cookies=False
        grab = build_grab()
        grab.setup(reuse_cookies=False)
        self.server.add_response(Response(headers=[("Set-Cookie", "foo=bar")]))
        doc = grab.request(self.server.get_url())
        self.assertTrue(any(x.name == "foo" and x.value == "bar" for x in doc.cookies))
        self.server.add_response(Response())
        grab.request(self.server.get_url())
        self.assertFalse(self.server.request.cookies)

        # Test something
        grab = build_grab()
        grab.setup(reuse_cookies=True)
        self.server.add_response(Response(headers=[("Set-Cookie", "foo=bar")]))
        doc = grab.request(self.server.get_url())
        self.assertTrue(any(x.name == "foo" and x.value == "bar" for x in doc.cookies))
        grab.clear_cookies()
        self.server.add_response(Response())
        grab.request(self.server.get_url())
        self.assertFalse(self.server.request.cookies)

    def test_redirect_session(self):
        grab = build_grab()
        self.server.add_response(Response(headers=[("Set-Cookie", "foo=bar")]))
        doc = grab.request(self.server.get_url())
        self.assertTrue(any(x.name == "foo" and x.value == "bar" for x in doc.cookies))

        # Setup one-time redirect
        grab = build_grab()
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
        self.assertTrue(any(x.name == "foo" and x.value == "bar" for x in grab.cookies))

    # def test_load_dump(self):
    #    with temp_file() as tmp_file:
    #        self.server.add_response(Response())
    #        grab = build_grab()
    #        cookies = {"foo": "bar", "spam": "ham"}
    #        grab.setup(cookies=cookies)
    #        grab.request(self.server.get_url())
    #        grab.cookies.save_to_file(tmp_file)
    #        with open(tmp_file, encoding="utf-8") as inp:
    #            self.assertEqual(
    #                set(cookies.items()),
    #                {(x["name"], x["value"]) for x in json.load(inp)},
    #            )

    #        self.server.add_response(Response())
    #        grab = build_grab()
    #        cookies = {"foo": "bar", "spam": "begemot"}
    #        grab.setup(cookies=cookies)
    #        grab.request(self.server.get_url())
    #        grab.cookies.save_to_file(tmp_file)
    #        with open(tmp_file, encoding="utf-8") as inp:
    #            self.assertEqual(
    #                set(cookies.items()),
    #                {(x["name"], x["value"]) for x in json.load(inp)},
    #            )

    #        # Test load cookies
    #        grab = build_grab()
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
    #    grab = build_grab()
    #    self.assertRaises(GrabMisuseError, grab.cookies.update, None)
    #    self.assertRaises(GrabMisuseError, grab.cookies.update, "asdf")
    #    self.assertRaises(GrabMisuseError, grab.cookies.update, ["asdf"])

    def test_path(self):
        self.server.add_response(
            Response(
                headers=[
                    ("Set-Cookie", "foo=1; path=/;"),
                    ("Set-Cookie", "bar=1; path=/admin;"),
                ]
            )
        )

        # work with "/" path
        grab = build_grab()
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

    #        grab = build_grab()
    #        grab.cookies.load_from_file(tmp_file)

    #        cookies = {
    #            "foo": "bar2",
    #            "sex": "male",
    #        }

    #        grab.setup(cookies=cookies)
    #        grab.request(self.server.get_url())
    #        self.assertEqual(2, len(self.server.get_request().cookies))

    # def test_cookie_merging_replace(self):
    #    grab = build_grab()
    #    grab.cookies.set("foo", "bar", "localhost")
    #    grab.cookies.set("foo", "bar2", "localhost")
    #    self.assertEqual(1, len(grab.cookies.items()))

    #    # Empty domain as same as localhost because internally
    #    # localhost replaced with empty string
    #    grab.cookies.set("foo", "bar3", "")
    #    self.assertEqual(1, len(grab.cookies.items()))

    #    grab.cookies.set("foo", "bar2", domain="ya.ru")
    #    self.assertEqual(2, len(grab.cookies.items()))

    def test_unicode_cookie(self):
        grab = build_grab()

        def callback():
            return b"HTTP/1.0 200 OK\nSet-Cookie: preved=%s\n\n" % "медвед".encode(
                "utf-8"
            )

        self.server.add_response(Response(raw_callback=callback))
        self.server.add_response(Response())
        # request page and receive unicode cookie
        grab.request(self.server.get_url())
        # request page one more time, sending cookie
        # should not fail
        grab.request(self.server.get_url())
