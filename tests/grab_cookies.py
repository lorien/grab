# coding: utf-8
import json
import pickle

from grab.cookie import CookieManager, create_cookie
from grab.error import GrabMisuseError
from test_server import Request, Response
from tests.util import BaseGrabTestCase, build_grab, only_grab_transport, temp_file


class TestCookies(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_parsing_response_cookies(self):
        grab = build_grab()
        self.server.add_response(
            Response(headers=[("Set-Cookie", "foo=bar;1=2")]), count=1
        )
        grab.go(self.server.get_url())
        self.assertEqual(grab.doc.cookies["foo"], "bar")

    def test_multiple_cookies(self):
        grab = build_grab()
        self.server.add_response(Response(), count=1)
        grab.setup(cookies={"foo": "1", "bar": "2"})
        grab.go(self.server.get_url())
        req = self.server.get_request()
        self.assertEqual(
            set(
                [
                    "{}={}".format(x.key, x.value)
                    for x in self.server.get_request().cookies.values()
                ]
            ),
            set(["foo=1", "bar=2"]),
        )

    def test_session(self):
        # Test that if Grab gets some cookies from the server
        # then it sends it back
        grab = build_grab()
        grab.setup(reuse_cookies=True)
        self.server.add_response(Response(headers=[("Set-Cookie", "foo=bar")]), count=1)
        grab.go(self.server.get_url())
        self.assertEqual(grab.doc.cookies["foo"], "bar")

        self.server.add_response(Response(), count=1)
        grab.go(self.server.get_url())
        req = self.server.get_request()
        self.assertEqual(str(req.cookies), "Set-Cookie: foo=bar")

        self.server.add_response(Response(), count=1)
        grab.go(self.server.get_url())
        req = self.server.get_request()
        self.assertEqual(str(req.cookies), "Set-Cookie: foo=bar")

        # Test reuse_cookies=False
        grab = build_grab()
        grab.setup(reuse_cookies=False)
        self.server.add_response(Response(headers=[("Set-Cookie", "foo=baz")]), count=1)
        grab.go(self.server.get_url())
        self.assertEqual(grab.doc.cookies["foo"], "baz")

        self.server.add_response(Response(), count=1)
        grab.go(self.server.get_url())
        req = self.server.get_request()
        self.assertTrue(len(req.cookies) == 0)

        # Test something
        grab = build_grab()
        grab.setup(reuse_cookies=True)
        self.server.add_response(Response(headers=[("Set-Cookie", "foo=bar")]), count=1)
        grab.go(self.server.get_url())
        self.assertEqual(grab.doc.cookies["foo"], "bar")
        grab.clear_cookies()

        self.server.add_response(Response(), count=-1)
        grab.go(self.server.get_url())
        req = self.server.get_request()
        self.assertTrue(len(req.cookies) == 0)

    def test_redirect_session(self):
        grab = build_grab()
        self.server.add_response(Response(headers=[("Set-Cookie", "foo=bar")]), count=1)
        grab.go(self.server.get_url())
        self.assertEqual(grab.doc.cookies["foo"], "bar")

        # Setup one-time redirect
        grab = build_grab()
        self.server.add_response(
            Response(
                status=302,
                headers=[
                    ("Location", self.server.get_url()),
                    ("Set-Cookie", "foo=bar"),
                ],
            ),
            count=1,
        )
        self.server.add_response(Response(), count=1)
        grab.go(self.server.get_url())
        req = self.server.get_request()
        self.assertEqual(req.cookies["foo"].value, "bar")

    def test_load_dump(self):
        with temp_file() as tmp_file:
            grab = build_grab()
            cookies = {"foo": "bar", "spam": "ham"}
            self.server.add_response(Response())
            grab.setup(cookies=cookies)
            grab.go(self.server.get_url())
            grab.cookies.save_to_file(tmp_file)
            with open(tmp_file) as inp:
                self.assertEqual(
                    set(cookies.items()),
                    set((x["name"], x["value"]) for x in json.load(inp)),
                )

            grab = build_grab()
            cookies = {"foo": "bar", "spam": "begemot"}
            grab.setup(cookies=cookies)
            self.server.add_response(Response())
            grab.go(self.server.get_url())
            grab.cookies.save_to_file(tmp_file)
            with open(tmp_file) as inp:
                self.assertEqual(
                    set(cookies.items()),
                    set((x["name"], x["value"]) for x in json.load(inp)),
                )

            # Test load cookies
            grab = build_grab()
            cookies = [
                {"name": "foo", "value": "bar", "domain": self.server.address},
                {"name": "spam", "value": "begemot", "domain": self.server.address},
            ]
            with open(tmp_file, "w") as out:
                json.dump(cookies, out)
            grab.cookies.load_from_file(tmp_file)
            self.assertEqual(
                set(grab.cookies.items()), set((x["name"], x["value"]) for x in cookies)
            )

    def test_cookiefile_empty(self):
        with temp_file() as tmp_file:
            grab = build_grab()
            # Empty file should not raise Exception
            with open(tmp_file, "w") as out:
                out.write("")
            grab.setup(cookiefile=tmp_file)
            self.server.add_response(Response())
            grab.go(self.server.get_url())

    def test_cookiefile(self):
        with temp_file() as tmp_file:
            grab = build_grab()

            cookies = [{"name": "spam", "value": "ham", "domain": self.server.address}]
            with open(tmp_file, "w") as out:
                json.dump(cookies, out)

            # One cookie are sent in server reponse
            # Another cookies is passed via the `cookiefile` option
            self.server.add_response(
                Response(headers=[("Set-Cookie", "godzilla=monkey")]), count=1
            )
            grab.setup(cookiefile=tmp_file, debug=True)
            grab.go(self.server.get_url())
            req = self.server.get_request()
            self.assertEqual(req.cookies["spam"].value, "ham")

            # This is correct reslt of combining two cookies
            merged_cookies = [("godzilla", "monkey"), ("spam", "ham")]

            # grab.cookies should contains merged cookies
            self.assertEqual(set(merged_cookies), set(grab.cookies.items()))

            # `cookiefile` file should contains merged cookies
            with open(tmp_file) as inp:
                self.assertEqual(
                    set(merged_cookies),
                    set((x["name"], x["value"]) for x in json.load(inp)),
                )

            # Just ensure it works
            self.server.add_response(Response())
            grab.go(self.server.get_url())

    @only_grab_transport("pycurl")
    def test_manual_dns(self):
        import pycurl

        grab = build_grab()
        grab.setup_transport("pycurl")
        grab.transport.curl.setopt(
            pycurl.RESOLVE, ["foo:%d:127.0.0.1" % self.server.port]
        )
        self.server.add_response(Response(data="zzz"), count=1, method="get")
        grab.go("http://foo:%d/" % self.server.port)
        self.assertEqual(b"zzz", grab.doc.body)

    @only_grab_transport("pycurl")
    def test_different_domains(self):
        import pycurl

        grab = build_grab()
        names = [
            "foo:%d:127.0.0.1" % self.server.port,
            "bar:%d:127.0.0.1" % self.server.port,
        ]
        grab.init_transport()
        grab.transport.curl.setopt(pycurl.RESOLVE, names)

        self.server.add_response(Response(headers=[("Set-Cookie", "foo=foo")]), count=1)
        grab.go("http://foo:%d" % self.server.port)
        self.assertEqual(dict(grab.doc.cookies.items()), {"foo": "foo"})

        self.server.add_response(Response(headers=[("Set-Cookie", "bar=bar")]), count=1)
        grab.go("http://bar:%d" % self.server.port)

        # response.cookies contains cookies from both domains
        # because it just accumulates cookies over time
        self.assertEqual(dict(grab.doc.cookies.items()), {"foo": "foo", "bar": "bar"})

    @only_grab_transport("pycurl")
    def test_cookie_domain(self):
        import pycurl

        grab = build_grab()
        names = [
            "example.com:%d:127.0.0.1" % self.server.port,
        ]
        grab.setup_transport("pycurl")
        grab.transport.curl.setopt(pycurl.RESOLVE, names)
        grab.cookies.set("foo", "bar", domain="example.com")
        self.server.add_response(Response())
        grab.go("http://example.com:%d/" % self.server.port)
        req = self.server.get_request()
        self.assertEqual("bar", req.cookies["foo"].value)

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
        import pycurl

        grab = build_grab(debug=True)
        names = [
            "foo.bar:%d:127.0.0.1" % self.server.port,
            "www.foo.bar:%d:127.0.0.1" % self.server.port,
        ]
        grab.init_transport()
        grab.transport.curl.setopt(pycurl.RESOLVE, names)

        self.server.add_response(
            Response(
                headers=[
                    (
                        "Set-Cookie",
                        "foo=foo; Domain=.foo.bar; "
                        "Expires=Wed, 13 Jan 2031 22:23:01 GMT;",
                    )
                ]
            ),
            count=2,
        )

        grab.go("http://foo.bar:%d" % self.server.port)
        self.assertEqual(dict(grab.doc.cookies.items()), {"foo": "foo"})

        grab.go("http://www.foo.bar:%d" % self.server.port)
        req = self.server.get_request()
        self.assertEqual("foo", req.cookies["foo"].value)
        self.assertEqual(dict(grab.doc.cookies.items()), {"foo": "foo"})

    def test_path_root(self):
        self.server.add_response(
            Response(
                headers=[
                    ("Set-Cookie", "foo=1; path=/;"),
                    ("Set-Cookie", "bar=1; path=/admin;"),
                ]
            ),
            count=2,
        )

        # work with "/" path
        grab = build_grab()
        # get cookies
        grab.go(self.server.get_url("/"))
        # submit received cookies
        grab.go(self.server.get_url("/"))
        req = self.server.get_request()
        self.assertEqual(1, len(req.cookies))

    def test_path_non_root(self):
        self.server.add_response(
            Response(
                headers=[
                    ("Set-Cookie", "foo=1; path=/;"),
                    ("Set-Cookie", "bar=1; path=/admin;"),
                ]
            ),
            count=2,
        )

        # work with "/admin" path
        grab = build_grab()
        # get cookies
        grab.go(self.server.get_url("/"))
        # submit received cookies
        grab.go(self.server.get_url("/admin/zz"))
        req = self.server.get_request()
        self.assertEqual(2, len(req.cookies))

    @only_grab_transport("pycurl")
    def test_common_case_www_domain(self):
        import pycurl

        grab = build_grab()
        names = [
            "www.foo.bar:%d:127.0.0.1" % self.server.port,
        ]
        grab.init_transport()
        grab.transport.curl.setopt(pycurl.RESOLVE, names)

        # Cookies are set for root domain (not for www subdomain)
        self.server.add_response(
            Response(
                headers=[
                    ("Set-Cookie", "foo=1; Domain=foo.bar;"),
                    ("Set-Cookie", "bar=2; Domain=.foo.bar;"),
                ]
            ),
            count=1,
        )

        # get cookies
        grab.go("http://www.foo.bar:%d" % self.server.port)

        # submit cookies
        self.server.add_response(Response(), count=1)
        grab.go("http://www.foo.bar:%d" % self.server.port)
        req = self.server.get_request()
        self.assertEqual("1", (req.cookies["foo"].value))
        req = self.server.get_request()
        self.assertEqual("2", (req.cookies["bar"].value))

    def test_cookie_merging_replace_with_cookies_option(self):
        with temp_file() as tmp_file:
            init_cookies = [
                {"name": "foo", "value": "bar", "domain": self.server.address}
            ]
            with open(tmp_file, "w") as out:
                json.dump(init_cookies, out)

            grab = build_grab(debug=True)
            grab.cookies.load_from_file(tmp_file)

            cookies = {
                "foo": "bar2",
                "sex": "male",
            }

            self.server.add_response(Response())
            grab.setup(cookies=cookies)
            grab.go(self.server.get_url())
            req = self.server.get_request()
            self.assertEqual(2, len(req.cookies.items()))

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
        self.server.add_response(
            Response(
                data="Z",
                headers=[
                    # fmt: off
                   ("Set-Cookie", u"preved=медвед".encode("utf-8")),
                    # fmt: on
                ],
            ),
            count=1,
        )
        # request page and receive unicode cookie
        grab.go(self.server.get_url())
        self.assertEqual(b"Z", grab.doc.body)

        ## request page one more time, sending cookie
        # self.server.add_response(Response(), count=1)
        # grab.go(self.server.get_url())
        ## does not work yet, because test_server does not correclty
        ## display request unicode cookies
        # req = self.server.get_request()
        # print(req.cookies)
        ## fmt: off
        # self.assertEqual(u"медвед", req.cookies["preved"].value)
        ## fmt: on
