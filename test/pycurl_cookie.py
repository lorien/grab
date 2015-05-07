# coding: utf-8
"""
This test case has written to help me
understand how pycurl lib works with cookies
"""
import pycurl
from six import BytesIO
from six.moves.http_cookiejar import CookieJar

from grab.error import GrabMisuseError
from test.util import BaseGrabTestCase
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

    def test_pycurl_cookies(self):
        self.server.response_once['code'] = 302
        self.server.response_once['cookies'] = {'foo': 'bar', '1': '2'}.items()
        self.server.response_once['headers'] = [
            ('Location', self.server.get_url())]
        self.server.response['get.data'] = 'foo'

        buf = BytesIO()
        header_buf = BytesIO()

        # Configure pycurl instance
        # Usually all these crap is automatically handled by the Grab
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.server.get_url())
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.setopt(pycurl.HEADERFUNCTION, header_buf.write)
        c.setopt(pycurl.FOLLOWLOCATION, 1)
        c.setopt(pycurl.COOKIEFILE, "")
        c.perform()
        self.assertEqual(b'foo', buf.getvalue())

        print(c.getinfo(pycurl.INFO_COOKIELIST))
        self.assertEquals(2, len(c.getinfo(pycurl.INFO_COOKIELIST)))

        # Just make another request and check that pycurl has
        # submitted two cookies
        c.setopt(pycurl.URL, self.server.get_url())
        c.perform()
        self.assertEquals(2, len(self.server.request['cookies']))

        # Erase cookies
        cookies = c.getinfo(pycurl.INFO_COOKIELIST)
        c.setopt(pycurl.COOKIELIST, "ALL")
        c.setopt(pycurl.URL, self.server.get_url())
        c.perform()
        self.assertEquals(0, len(self.server.request['cookies']))

        # Now let's try to setup pycurl with cookies
        # saved into `cookies` variable
        for cookie in cookies:
            c.setopt(pycurl.COOKIELIST, cookie)
        c.setopt(pycurl.URL, self.server.get_url())
        c.perform()
        self.assertEquals(2, len(self.server.request['cookies']))
        self.assertEquals('bar', self.server.request['cookies']['foo'].value)
        self.assertEquals(set(('foo', '1')),
                          set(self.server.request['cookies'].keys()))

        # Ok, now let's create third cookies that is binded to
        # the path /place, put this cookie into curl object
        # and submit request to /
        # pycurl should not send third cookie
        cookie = '\t'.join((self.server.address,
                            'FALSE', '/place', 'FALSE', '0', 'no', 'way'))
        c.setopt(pycurl.COOKIELIST, cookie)
        c.setopt(pycurl.URL, self.server.get_url())
        c.perform()
        self.assertEquals(set(('foo', '1')),
                          set(self.server.request['cookies'].keys()))

        # Ok, now send request to /place
        c.setopt(pycurl.URL, self.server.get_url('/place'))
        c.perform()
        self.assertEquals(set(('foo', '1', 'no')),
                          set(self.server.request['cookies'].keys()))

        # Now, check that not all cookies set with cookieslist
        # are submitted
        c.setopt(pycurl.COOKIELIST, "ALL")
        c.setopt(pycurl.URL, self.server.get_url())
        c.setopt(pycurl.COOKIELIST, "Set-Cookie: 1=2; domain=microsoft.com")
        c.setopt(pycurl.COOKIELIST, "Set-Cookie: 3=4")
        c.setopt(pycurl.COOKIELIST, "Set-Cookie: 5=6")
        c.perform()
        self.assertEquals(2, len(self.server.request['cookies']))

    def test_cookie(self):
        create_cookie('foo', 'bar', self.server.address)
        self.assertRaises(GrabMisuseError, create_cookie,
                          'foo', 'bar', self.server.address, x='y')

    def test_cookiejar(self):
        c1 = create_cookie('foo', 'bar', self.server.address)
        c2 = create_cookie('foo', 'bar', self.server.address)
        self.assertFalse(c1 == c2)

        c = create_cookie('foo', 'bar', domain='.dumpz.org')
        self.assertEquals(c.domain, '.dumpz.org')

        cj = CookieJar()
        cj.set_cookie(create_cookie('foo', 'bar', domain='foo.com'))
        cj.set_cookie(create_cookie('foo', 'bar', domain='bar.com'))
        self.assertEqual(len(cj), 2)
