# coding: utf-8
"""
This test case has written to help me
understand how pycurl lib works with cookies
"""
from six.moves.http_cookiejar import CookieJar
from six import BytesIO
from test_server import Response

from tests.util import BaseGrabTestCase, only_grab_transport
from grab.error import GrabMisuseError
from grab.cookie import create_cookie

# http://xiix.wordpress.com/2006/03/23/mozillafirefox-cookie-format/
# http://curl.haxx.se/libcurl/c/curl_easy_setopt.html
# Cookie:
# * domain
# * whether or not all machines under that domain can read
# the cookie’s information.
# * path
# * Secure Flag: whether or not a secure connection (HTTPS)
# is required to read the cookie.
# * exp. timestamp
# * name
# * value


class TestCookies(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    @only_grab_transport("pycurl")
    def test_pycurl_cookies(self):
        import pycurl  # pylint: disable=import-outside-toplevel

        self.server.add_response(
            Response(
                status=302,
                headers=[
                    ("set-cookie", "foo=bar"),
                    ("set-cookie", "baz=gaz"),
                    ("location", self.server.get_url()),
                ],
            )
        )
        self.server.add_response(Response(), count=7)

        buf = BytesIO()
        header_buf = BytesIO()

        # Configure pycurl instance
        # Usually all these crap is automatically handled by the Grab
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, self.server.get_url())
        curl.setopt(pycurl.WRITEFUNCTION, buf.write)
        curl.setopt(pycurl.HEADERFUNCTION, header_buf.write)
        curl.setopt(pycurl.FOLLOWLOCATION, 1)
        curl.setopt(pycurl.COOKIEFILE, "")
        curl.perform()
        self.assertEqual(2, len(curl.getinfo(pycurl.INFO_COOKIELIST)))

        # Just make another request and check that pycurl has
        # submitted two cookies
        curl.setopt(pycurl.URL, self.server.get_url())
        curl.perform()
        self.assertEqual(2, len(self.server.get_request().cookies))

        # Rember and then erase cookies
        cookies = curl.getinfo(pycurl.INFO_COOKIELIST)
        curl.setopt(pycurl.COOKIELIST, "ALL")
        curl.setopt(pycurl.URL, self.server.get_url())
        curl.perform()
        self.assertEqual(0, len(self.server.get_request().cookies))

        # Now let's try to setup pycurl with cookies
        # saved into `cookies` variable
        for cookie in cookies:
            curl.setopt(pycurl.COOKIELIST, cookie)
        curl.setopt(pycurl.URL, self.server.get_url())
        curl.perform()
        self.assertEqual(2, len(self.server.get_request().cookies))
        self.assertEqual("bar", self.server.get_request().cookies["foo"].value)
        self.server.get_request()
        self.assertEqual(
            set(("foo", "baz")), set(self.server.get_request().cookies.keys())
        )

        # Ok, now let's create third cookies that is binded to
        # the path /place, put this cookie into curl object
        # and submit request to /
        # pycurl should not send third cookie
        cookie = "\t".join(
            (self.server.address, "FALSE", "/place", "FALSE", "0", "no", "way")
        )
        curl.setopt(pycurl.COOKIELIST, cookie)
        curl.setopt(pycurl.URL, self.server.get_url())
        curl.perform()
        self.assertEqual(
            set(("foo", "baz")), set(self.server.get_request().cookies.keys())
        )

        # Ok, now send request to /place
        curl.setopt(pycurl.URL, self.server.get_url("/place"))
        curl.perform()
        self.assertEqual(
            set(("foo", "baz", "no")), set(self.server.get_request().cookies.keys())
        )

        # Now, check that not all cookies set with cookieslist
        # are submitted
        curl.setopt(pycurl.COOKIELIST, "ALL")
        curl.setopt(pycurl.URL, self.server.get_url())
        curl.setopt(pycurl.COOKIELIST, "Set-Cookie: 1=2; domain=microsoft.com")
        curl.setopt(pycurl.COOKIELIST, "Set-Cookie: 3=4")
        curl.setopt(pycurl.COOKIELIST, "Set-Cookie: 5=6")
        curl.perform()
        self.assertEqual(2, len(self.server.get_request().cookies))

    def test_cookie(self):
        create_cookie("foo", "bar", self.server.address)
        self.assertRaises(
            GrabMisuseError, create_cookie, "foo", "bar", self.server.address, x="y"
        )

    def test_cookiejar(self):
        cookie1 = create_cookie("foo", "bar", self.server.address)
        cookie2 = create_cookie("foo", "bar", self.server.address)
        self.assertFalse(cookie1 == cookie2)

        cookie0 = create_cookie("foo", "bar", domain=".dumpz.org")
        self.assertEqual(cookie0.domain, ".dumpz.org")

        jar = CookieJar()
        jar.set_cookie(create_cookie("foo", "bar", domain="foo.com"))
        jar.set_cookie(create_cookie("foo", "bar", domain="bar.com"))
        self.assertEqual(len(jar), 2)
