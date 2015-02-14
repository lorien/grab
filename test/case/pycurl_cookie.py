# coding: utf-8
"""
This test case has written to help me
understand how pycurl lib works with cookies
"""
from unittest import TestCase
import pycurl
try:
    from cStringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO
try:
    from cookielib import CookieJar, Cookie
except ImportError:
    from http.cookiejar import CookieJar, Cookie


from test.server import SERVER
from grab.cookie import create_cookie

# http://xiix.wordpress.com/2006/03/23/mozillafirefox-cookie-format/
# http://curl.haxx.se/libcurl/c/curl_easy_setopt.html
# Cookie:
# * domain
# * whether or not all machines under that domain can read the cookie’s information.
# * path
# * Secure Flag: whether or not a secure connection (HTTPS) is required to read the cookie.
# * exp. timestamp
# * name
# * value

class TestCookies(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_pycurl_cookies(self):
        SERVER.RESPONSE_ONCE['code'] = 302
        SERVER.RESPONSE_ONCE['cookies'] = {'foo': 'bar', '1': '2'}
        SERVER.RESPONSE_ONCE['headers'].append(('Location', SERVER.BASE_URL))
        SERVER.RESPONSE['get'] = 'foo'

        buf = StringIO()
        header_buf = StringIO()
        cfile = StringIO()

        # Configure pycurl instance
        # Usually all these crap is automatically handled by the Grab
        c = pycurl.Curl()
        c.setopt(pycurl.URL, SERVER.BASE_URL)
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
        c.setopt(pycurl.URL, SERVER.BASE_URL)
        c.perform()
        self.assertEquals(2, len(SERVER.REQUEST['cookies']))

        # Erase cookies
        cookies = c.getinfo(pycurl.INFO_COOKIELIST)
        c.setopt(pycurl.COOKIELIST, "ALL")
        c.setopt(pycurl.URL, SERVER.BASE_URL)
        c.perform()
        self.assertEquals(0, len(SERVER.REQUEST['cookies']))

        # Now let's try to setup pycurl with cookies
        # saved into `cookies` variable
        for cookie in cookies:
            c.setopt(pycurl.COOKIELIST, cookie)
        c.setopt(pycurl.URL, SERVER.BASE_URL)
        c.perform()
        self.assertEquals(2, len(SERVER.REQUEST['cookies']))
        self.assertEquals('bar', SERVER.REQUEST['cookies']['foo'].value)
        self.assertEquals(set(('foo', '1')), set(SERVER.REQUEST['cookies'].keys()))

        # Ok, now let's create third cookies that is binded to
        # the path /place, put this cookie into curl object
        # and submit request to /
        # pycurl should not send third cookie
        cookie = '\t'.join(('localhost', 'FALSE', '/place', 'FALSE', '0', 'no', 'way'))
        c.setopt(pycurl.COOKIELIST, cookie)
        c.setopt(pycurl.URL, SERVER.BASE_URL)
        c.perform()
        self.assertEquals(set(('foo', '1')), set(SERVER.REQUEST['cookies'].keys()))

        # Ok, now send request to /place
        c.setopt(pycurl.URL, SERVER.BASE_URL + '/place')
        c.perform()
        self.assertEquals(set(('foo', '1', 'no')), set(SERVER.REQUEST['cookies'].keys()))

        # Now, check that not all cookies set with cookieslist
        # are submitted
        c.setopt(pycurl.COOKIELIST, "ALL")
        c.setopt(pycurl.URL, SERVER.BASE_URL)
        c.setopt(pycurl.COOKIELIST, "Set-Cookie: 1=2; domain=microsoft.com")
        c.setopt(pycurl.COOKIELIST, "Set-Cookie: 3=4")
        c.setopt(pycurl.COOKIELIST, "Set-Cookie: 5=6")
        c.perform()
        self.assertEquals(2, len(SERVER.REQUEST['cookies']))

    #def test_some_thing(self):
        #SERVER.RESPONSE['headers'].append(
            #('Set-Cookie', 'x=y; expires=Fri, 31 Dec 2020 23:59:59 GMT;'
                           #' path=/; domain=.foo.bar'),
        #)
        #SERVER.RESPONSE['get'] = 'foo'

        #buf = StringIO()
        #header_buf = StringIO()
        #cfile = StringIO()

        ## Configure pycurl instance
        ## Usually all these crap is automatically handled by the Grab
        #c = pycurl.Curl()
        #c.setopt(pycurl.URL, 'http://foo.bar:9876')#SERVER.BASE_URL)
        #c.setopt(pycurl.WRITEFUNCTION, buf.write)
        #c.setopt(pycurl.HEADERFUNCTION, header_buf.write)
        #c.setopt(pycurl.FOLLOWLOCATION, 1)
        #c.setopt(pycurl.COOKIEFILE, "")
        #c.perform()

        #print header_buf.getvalue()
        #print c.getinfo(pycurl.INFO_COOKIELIST)#[0]#.split('\t')

    def test_cookie(self):
        c = create_cookie('foo', 'bar')

        self.assertRaises(TypeError, lambda: create_cookie('foo', 'bar', x='y'))

    def test_cookiejar(self):
        c1 = create_cookie('foo', 'bar')
        c2 = create_cookie('foo', 'bar')
        self.assertFalse(c1 == c2)

        c = create_cookie('foo', 'bar', domain='.dumpz.org')
        self.assertEquals(c.domain, '.dumpz.org')

        cj = CookieJar()
        cj.set_cookie(create_cookie('foo', 'bar', domain='foo.com'))
        cj.set_cookie(create_cookie('foo', 'bar', domain='bar.com'))
        self.assertEqual(len(cj), 2)
