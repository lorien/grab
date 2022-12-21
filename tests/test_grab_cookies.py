import json
import pickle
from pprint import pprint  # pylint: disable=unused-import

from test_server import Response

from grab.cookie import CookieManager, create_cookie
from grab.error import GrabMisuseError
from tests.util import BaseGrabTestCase, build_grab, temp_file


class TestCookies(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_cookiefile(self):
        with temp_file() as tmp_file:
            grab = build_grab()

            cookies = [{"name": "spam", "value": "ham", "domain": self.server.address}]
            with open(tmp_file, "w", encoding="utf-8") as out:
                json.dump(cookies, out)

            # One cookie are sent in server response
            # Another cookies is passed via the `cookiefile` option
            self.server.add_response(
                Response(headers=[("Set-Cookie", "godzilla=monkey")])
            )
            grab.setup(cookiefile=tmp_file)
            grab.request(self.server.get_url())
            self.assertEqual(self.server.request.cookies["spam"].value, "ham")

            # This is correct reslt of combining two cookies
            merged_cookies = [("godzilla", "monkey"), ("spam", "ham")]

            # grab.cookies should contains merged cookies
            self.assertEqual(set(merged_cookies), set(grab.cookies.items()))

            # `cookiefile` file should contains merged cookies
            with open(tmp_file, encoding="utf-8") as inp:
                self.assertEqual(
                    set(merged_cookies),
                    {(x["name"], x["value"]) for x in json.load(inp)},
                )

            # Just ensure it works
            self.server.add_response(Response())
            grab.request(self.server.get_url())

    def test_parsing_response_cookies(self):
        grab = build_grab()
        self.server.add_response(
            Response(headers=[("Set-Cookie", "foo=bar"), ("Set-Cookie", "1=2")])
        )
        grab.request(self.server.get_url())
        self.assertEqual(grab.doc.cookies["foo"], "bar")

    def test_multiple_cookies(self):
        grab = build_grab()
        self.server.add_response(Response())
        grab.setup(cookies={"foo": "1", "bar": "2"})
        grab.request(self.server.get_url())
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
        grab.request(self.server.get_url())
        self.assertEqual(grab.doc.cookies["foo"], "bar")
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
        grab.request(self.server.get_url())
        self.assertEqual(grab.doc.cookies["foo"], "bar")
        self.server.add_response(Response())
        grab.request(self.server.get_url())
        self.assertFalse(self.server.request.cookies)

        # Test something
        grab = build_grab()
        grab.setup(reuse_cookies=True)
        self.server.add_response(Response(headers=[("Set-Cookie", "foo=bar")]))
        grab.request(self.server.get_url())
        self.assertEqual(grab.doc.cookies["foo"], "bar")
        grab.clear_cookies()
        self.server.add_response(Response())
        grab.request(self.server.get_url())
        self.assertFalse(self.server.request.cookies)

    def test_redirect_session(self):
        grab = build_grab()
        self.server.add_response(Response(headers=[("Set-Cookie", "foo=bar")]))
        grab.request(self.server.get_url())
        self.assertEqual(grab.doc.cookies["foo"], "bar")

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
        self.assertEqual(self.server.request.cookies["foo"].value, "bar")

    def test_load_dump(self):
        with temp_file() as tmp_file:
            self.server.add_response(Response())
            grab = build_grab()
            cookies = {"foo": "bar", "spam": "ham"}
            grab.setup(cookies=cookies)
            grab.request(self.server.get_url())
            grab.cookies.save_to_file(tmp_file)
            with open(tmp_file, encoding="utf-8") as inp:
                self.assertEqual(
                    set(cookies.items()),
                    {(x["name"], x["value"]) for x in json.load(inp)},
                )

            self.server.add_response(Response())
            grab = build_grab()
            cookies = {"foo": "bar", "spam": "begemot"}
            grab.setup(cookies=cookies)
            grab.request(self.server.get_url())
            grab.cookies.save_to_file(tmp_file)
            with open(tmp_file, encoding="utf-8") as inp:
                self.assertEqual(
                    set(cookies.items()),
                    {(x["name"], x["value"]) for x in json.load(inp)},
                )

            # Test load cookies
            grab = build_grab()
            cookies_list = [
                {"name": "foo", "value": "bar", "domain": self.server.address},
                {"name": "spam", "value": "begemot", "domain": self.server.address},
            ]
            with open(tmp_file, "w", encoding="utf-8") as out:
                json.dump(cookies_list, out)
            grab.cookies.load_from_file(tmp_file)
            self.assertEqual(
                set(grab.cookies.items()),
                {(x["name"], x["value"]) for x in cookies_list},
            )

    def test_cookiefile_empty(self):
        with temp_file() as tmp_file:
            self.server.add_response(Response())
            grab = build_grab()
            # Empty file should not raise Exception
            with open(tmp_file, "w", encoding="utf-8") as out:
                out.write("")
            grab.setup(cookiefile=tmp_file)
            grab.request(self.server.get_url())

    def test_update_invalid_cookie(self):
        grab = build_grab()
        self.assertRaises(GrabMisuseError, grab.cookies.update, None)
        self.assertRaises(GrabMisuseError, grab.cookies.update, "asdf")
        self.assertRaises(GrabMisuseError, grab.cookies.update, ["asdf"])

    def test_from_cookie_list(self):
        cookie = create_cookie("foo", "bar", self.server.address)
        mgr = CookieManager.from_cookie_list([cookie])
        test_cookie = [x for x in mgr.cookiejar if x.name == "foo"][0]
        self.assertEqual(cookie.name, test_cookie.name)

        mgr = CookieManager.from_cookie_list([])
        self.assertEqual(0, len(list(mgr.cookiejar)))

    def test_pickle_serialization(self):
        cookie = create_cookie("foo", "bar", self.server.address)
        mgr = CookieManager.from_cookie_list([cookie])
        dump = pickle.dumps(mgr)
        mgr2 = pickle.loads(dump)
        self.assertEqual(list(mgr.cookiejar)[0].value, list(mgr2.cookiejar)[0].value)

    def test_get_item(self):
        cookie = create_cookie("foo", "bar", self.server.address)
        mgr = CookieManager.from_cookie_list([cookie])
        self.assertEqual("bar", mgr["foo"])
        self.assertRaises(KeyError, lambda: mgr["zzz"])

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

    def test_cookie_merging_replace_with_cookies_option(self):
        with temp_file() as tmp_file:
            self.server.add_response(Response())
            init_cookies = [
                {"name": "foo", "value": "bar", "domain": self.server.address}
            ]
            with open(tmp_file, "w", encoding="utf-8") as out:
                json.dump(init_cookies, out)

            grab = build_grab()
            grab.cookies.load_from_file(tmp_file)

            cookies = {
                "foo": "bar2",
                "sex": "male",
            }

            grab.setup(cookies=cookies)
            grab.request(self.server.get_url())
            self.assertEqual(2, len(self.server.get_request().cookies))

    def test_cookie_merging_replace(self):
        grab = build_grab()
        grab.cookies.set("foo", "bar", "localhost")
        grab.cookies.set("foo", "bar2", "localhost")
        self.assertEqual(1, len(grab.cookies.items()))

        # Empty domain as same as localhost because internally
        # localhost replaced with empty string
        grab.cookies.set("foo", "bar3", "")
        self.assertEqual(1, len(grab.cookies.items()))

        grab.cookies.set("foo", "bar2", domain="ya.ru")
        self.assertEqual(2, len(grab.cookies.items()))

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
