import json
import pickle
from pprint import pprint

from test_server import Response

from grab.error import GrabMisuseError
from grab.cookie import CookieManager, create_cookie

from tests.util import temp_file, build_grab, only_grab_transport
from tests.util import BaseGrabTestCase


class TestCookies(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_parsing_response_cookies(self):
        grab = build_grab()
        self.server.add_response(
            Response(headers=[("Set-Cookie", "foo=bar"), ("Set-Cookie", "1=2")])
        )
        grab.go(self.server.get_url())
        self.assertEqual(grab.doc.cookies["foo"], "bar")

    def test_multiple_cookies(self):
        grab = build_grab()
        self.server.add_response(Response())
        grab.setup(cookies={"foo": "1", "bar": "2"})
        grab.go(self.server.get_url())
        self.assertEqual(
            set((x.key, x.value) for x in self.server.request.cookies.values()),
            set([("foo", "1"), ("bar", "2")]),
        )

    def test_session(self):
        # Test that if Grab gets some cookies from the server
        # then it sends it back
        grab = build_grab()
        grab.setup(reuse_cookies=True)
        self.server.add_response(Response(headers=[("Set-Cookie", "foo=bar")]))
        grab.go(self.server.get_url())
        self.assertEqual(grab.doc.cookies["foo"], "bar")
        self.server.add_response(Response())
        grab.go(self.server.get_url())
        self.assertEqual(
            set([("foo", "bar")]),
            set((x.key, x.value) for x in self.server.request.cookies.values()),
        )
        self.server.add_response(Response())
        grab.go(self.server.get_url())
        self.assertEqual(
            set([("foo", "bar")]),
            set((x.key, x.value) for x in self.server.request.cookies.values()),
        )

        # Test reuse_cookies=False
        grab = build_grab()
        grab.setup(reuse_cookies=False)
        self.server.add_response(Response(headers=[("Set-Cookie", "foo=bar")]))
        grab.go(self.server.get_url())
        self.assertEqual(grab.doc.cookies["foo"], "bar")
        self.server.add_response(Response())
        grab.go(self.server.get_url())
        self.assertTrue(len(self.server.request.cookies) == 0)

        # Test something
        grab = build_grab()
        grab.setup(reuse_cookies=True)
        self.server.add_response(Response(headers=[("Set-Cookie", "foo=bar")]))
        grab.go(self.server.get_url())
        self.assertEqual(grab.doc.cookies["foo"], "bar")
        grab.clear_cookies()
        self.server.add_response(Response())
        grab.go(self.server.get_url())
        self.assertTrue(len(self.server.request.cookies) == 0)

    def test_redirect_session(self):
        grab = build_grab()
        self.server.add_response(Response(headers=[("Set-Cookie", "foo=bar")]))
        grab.go(self.server.get_url())
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
        grab.go(self.server.get_url())
        self.assertEqual(self.server.request.cookies["foo"].value, "bar")

    def test_load_dump(self):
        with temp_file() as tmp_file:
            self.server.add_response(Response())
            grab = build_grab()
            cookies = {"foo": "bar", "spam": "ham"}
            grab.setup(cookies=cookies)
            grab.go(self.server.get_url())
            grab.cookies.save_to_file(tmp_file)
            with open(tmp_file, encoding="utf-8") as inp:
                self.assertEqual(
                    set(cookies.items()),
                    set((x["name"], x["value"]) for x in json.load(inp)),
                )

            self.server.add_response(Response())
            grab = build_grab()
            cookies = {"foo": "bar", "spam": u"begemot"}
            grab.setup(cookies=cookies)
            grab.go(self.server.get_url())
            grab.cookies.save_to_file(tmp_file)
            with open(tmp_file, encoding="utf-8") as inp:
                self.assertEqual(
                    set(cookies.items()),
                    set((x["name"], x["value"]) for x in json.load(inp)),
                )

            # Test load cookies
            grab = build_grab()
            cookies = [
                {"name": "foo", "value": "bar", "domain": self.server.address},
                {"name": "spam", "value": u"begemot", "domain": self.server.address},
            ]
            with open(tmp_file, "w", encoding="utf-8") as out:
                json.dump(cookies, out)
            grab.cookies.load_from_file(tmp_file)
            self.assertEqual(
                set(grab.cookies.items()), set((x["name"], x["value"]) for x in cookies)
            )

    def test_cookiefile_empty(self):
        with temp_file() as tmp_file:
            self.server.add_response(Response())
            grab = build_grab()
            # Empty file should not raise Exception
            with open(tmp_file, "w", encoding="utf-8") as out:
                out.write("")
            grab.setup(cookiefile=tmp_file)
            grab.go(self.server.get_url())

    def test_cookiefile(self):
        with temp_file() as tmp_file:
            grab = build_grab()

            cookies = [{"name": "spam", "value": "ham", "domain": self.server.address}]
            with open(tmp_file, "w", encoding="utf-8") as out:
                json.dump(cookies, out)

            # One cookie are sent in server reponse
            # Another cookies is passed via the `cookiefile` option
            self.server.add_response(
                Response(headers=[("Set-Cookie", "godzilla=monkey")])
            )
            grab.setup(cookiefile=tmp_file, debug=True)
            grab.go(self.server.get_url())
            self.assertEqual(self.server.request.cookies["spam"].value, "ham")

            # This is correct reslt of combining two cookies
            merged_cookies = [("godzilla", "monkey"), ("spam", "ham")]

            # grab.cookies should contains merged cookies
            self.assertEqual(set(merged_cookies), set(grab.cookies.items()))

            # `cookiefile` file should contains merged cookies
            with open(tmp_file, encoding="utf-8") as inp:
                self.assertEqual(
                    set(merged_cookies),
                    set((x["name"], x["value"]) for x in json.load(inp)),
                )

            # Just ensure it works
            self.server.add_response(Response())
            grab.go(self.server.get_url())

    @only_grab_transport("pycurl")
    def test_manual_dns(self):
        import pycurl  # pylint: disable=import-outside-toplevel

        grab = build_grab()
        grab.setup_transport("pycurl")
        grab.transport.curl.setopt(
            pycurl.RESOLVE, ["foo:%d:127.0.0.1" % self.server.port]
        )
        self.server.add_response(Response(data=b"zzz"))
        grab.go("http://foo:%d/" % self.server.port)
        self.assertEqual(b"zzz", grab.doc.body)

    # @only_grab_transport("pycurl")
    # def test_different_domains(self):
    #    import pycurl  # pylint: disable=import-outside-toplevel

    #    grab = build_grab()
    #    names = [
    #        "foo:%d:127.0.0.1" % self.server.port,
    #        "bar:%d:127.0.0.1" % self.server.port,
    #    ]
    #    grab.setup_transport("pycurl")
    #    grab.transport.curl.setopt(pycurl.RESOLVE, names)

    #    self.server.add_response(Response(headers=[("Set-Cookie", "foo=foo")]))
    #    grab.go("http://foo:%d" % self.server.port)
    #    self.assertEqual(dict(grab.doc.cookies.items()), {"foo": "foo"})

    #    self.server.add_response(Response(headers=[("Set-Cookie", "bar=bar")]))
    #    grab.go("http://bar:%d" % self.server.port)
    #    self.assertEqual(dict(grab.doc.cookies.items()), {"bar": "bar"})

    #    # That does not hold anymore, I guess I have fixed it
    #    # # response.cookies contains cookies from both domains
    #    # # because it just accumulates cookies over time
    #    # # self.assertEqual(
    #    # #     dict(grab.doc.cookies.items()), {"foo": "foo", "bar": "bar"}
    #    # # )

    @only_grab_transport("pycurl")
    def test_cookie_domain(self):
        import pycurl  # pylint: disable=import-outside-toplevel

        grab = build_grab()
        names = [
            "example.com:%d:127.0.0.1" % self.server.port,
        ]
        grab.setup_transport("pycurl")
        grab.transport.curl.setopt(pycurl.RESOLVE, names)
        grab.cookies.set("foo", "bar", domain="example.com")
        grab.go("http://example.com:%d/" % self.server.port)

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

    @only_grab_transport("pycurl")
    def test_dot_domain(self):
        import pycurl  # pylint: disable=import-outside-toplevel

        grab = build_grab(debug=True)
        names = [
            "foo.bar:%d:127.0.0.1" % self.server.port,
            "www.foo.bar:%d:127.0.0.1" % self.server.port,
        ]
        grab.setup_transport("pycurl")
        grab.transport.curl.setopt(pycurl.RESOLVE, names)

        self.server.add_response(
            Response(
                headers=[
                    (
                        "Set-Cookie",
                        (
                            "foo=foo; Domain=.foo.bar;"
                            " Expires=Wed, 13 Jan 3000 22:23:01 GMT;"
                        ),
                    )
                ]
            ),
            count=2,
        )

        grab.go("http://www.foo.bar:%d" % self.server.port)
        self.assertEqual(dict(grab.doc.cookies.items()), {"foo": "foo"})
        pprint(grab.doc.cookies.get_dict())

        grab.go("http://www.foo.bar:%d" % self.server.port)
        pprint(self.server.request)
        self.assertEqual("foo", self.server.request.cookies.get("foo").value)

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
        grab.go(self.server.get_url("/"))

        self.server.add_response(Response())
        # submit received cookies
        grab.go(self.server.get_url("/"))
        self.assertEqual(1, len(self.server.request.cookies))

        self.server.add_response(Response())
        # work with "/admin" path
        grab.go(self.server.get_url("/admin/zz"))
        self.assertEqual(2, len(self.server.request.cookies))

    @only_grab_transport("pycurl")
    def test_common_case_www_domain(self):
        import pycurl  # pylint: disable=import-outside-toplevel

        grab = build_grab()
        names = [
            "www.foo.bar:%d:127.0.0.1" % self.server.port,
        ]
        grab.setup_transport("pycurl")
        grab.transport.curl.setopt(pycurl.RESOLVE, names)

        # Cookies are set for root domain (not for www subdomain)
        self.server.add_response(
            Response(
                headers=[
                    ("Set-Cookie", "foo=1; Domain=foo.bar;"),
                    ("Set-Cookie", "bar=2; Domain=.foo.bar;"),
                ]
            )
        )
        self.server.add_response(Response())

        # get cookies
        grab.go("http://www.foo.bar:%d" % self.server.port)
        # submit cookies
        grab.go("http://www.foo.bar:%d" % self.server.port)
        self.assertEqual("1", (self.server.request.cookies.get("foo").value))
        self.assertEqual("2", (self.server.request.cookies.get("bar").value))

    def test_cookie_merging_replace_with_cookies_option(self):
        with temp_file() as tmp_file:
            self.server.add_response(Response())
            init_cookies = [
                {"name": "foo", "value": "bar", "domain": self.server.address}
            ]
            with open(tmp_file, "w", encoding="utf-8") as out:
                json.dump(init_cookies, out)

            grab = build_grab(debug=True)
            grab.cookies.load_from_file(tmp_file)

            cookies = {
                "foo": "bar2",
                "sex": "male",
            }

            grab.setup(cookies=cookies)
            grab.go(self.server.get_url())
            self.assertEqual(2, len(self.server.get_request().cookies))

    def test_cookie_merging_replace(self):
        grab = build_grab()
        grab.cookies.set("foo", "bar", "localhost")
        grab.cookies.set("foo", "bar2", "localhost")
        self.assertEqual(1, len(grab.cookies.items()))

        # Empty domain as same as localhost becuase internally
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
        grab.go(self.server.get_url())
        # request page one more time, sending cookie
        # should not fail
        grab.go(self.server.get_url())
        # does not work yet, because test_server does not correclty
        # display request unicode cookies
        # self.assertEqual(
        # u'медвед', self.server.request['cookies']['preved']['value']
        # )
