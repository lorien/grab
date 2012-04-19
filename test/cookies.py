# coding: utf-8
from unittest import TestCase
import string
import json

from grab import Grab, GrabMisuseError
from util import (FakeServerThread, BASE_URL, RESPONSE, REQUEST,
                  RESPONSE_ONCE_HEADERS, TMP_FILE, GRAB_TRANSPORT)

class TestCookies(TestCase):
    def setUp(self):
        FakeServerThread().start()

    def test_cookies_parsing(self):
        g = Grab(transport=GRAB_TRANSPORT)
        RESPONSE['cookies'] = {'foo': 'bar', '1': '2'}
        g.go(BASE_URL)
        self.assertEqual(g.response.cookies['foo'], 'bar')

    def test_multiple_cookies(self):
        g = Grab(transport=GRAB_TRANSPORT)
        RESPONSE['cookies'] = {}
        g.setup(cookies={'foo': '1', 'bar': '2'})
        g.go(BASE_URL)
        self.assertEqual(
            set(map(string.strip, REQUEST['headers']['Cookie'].split('; '))),
            set(['foo=1', 'bar=2']))

    def test_session(self):
        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(reuse_cookies=True)
        RESPONSE['cookies'] = {'foo': 'bar'}
        g.go(BASE_URL)
        self.assertEqual(g.response.cookies['foo'], 'bar')
        g.go(BASE_URL)
        self.assertEqual(REQUEST['headers']['Cookie'], 'foo=bar')
        g.go(BASE_URL)
        self.assertEqual(REQUEST['headers']['Cookie'], 'foo=bar')

        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(reuse_cookies=False)
        RESPONSE['cookies'] = {'foo': 'baz'}
        g.go(BASE_URL)
        self.assertEqual(g.response.cookies['foo'], 'baz')
        g.go(BASE_URL)
        self.assertTrue('Cookie' not in REQUEST['headers'])

        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(reuse_cookies=True)
        RESPONSE['cookies'] = {'foo': 'bar'}
        g.go(BASE_URL)
        self.assertEqual(g.response.cookies['foo'], 'bar')
        g.clear_cookies()
        g.go(BASE_URL)
        self.assertTrue('Cookie' not in REQUEST['headers'])

    def test_redirect_session(self):
        g = Grab(transport=GRAB_TRANSPORT)
        RESPONSE['cookies'] = {'foo': 'bar'}
        g.go(BASE_URL)
        self.assertEqual(g.response.cookies['foo'], 'bar')

        # Setup one-time redirect
        g = Grab(transport=GRAB_TRANSPORT)
        RESPONSE['cookies'] = {}
        RESPONSE_ONCE_HEADERS.append(('Location', BASE_URL))
        RESPONSE_ONCE_HEADERS.append(('Set-Cookie', 'foo=bar'))
        RESPONSE['once_code'] = 302
        g.go(BASE_URL)
        self.assertEqual(REQUEST['headers']['Cookie'], 'foo=bar')

    def test_load_dump(self):
        g = Grab(transport=GRAB_TRANSPORT)
        cookies = {'foo': 'bar', 'spam': 'ham'}
        g.setup(cookies=cookies)
        g.dump_cookies(TMP_FILE)
        self.assertEqual(set(cookies.items()), set(json.load(open(TMP_FILE)).items()))

        # Test non-ascii
        g = Grab(transport=GRAB_TRANSPORT)
        cookies = {'foo': 'bar', 'spam': u'бегемот'}
        g.setup(cookies=cookies)
        g.dump_cookies(TMP_FILE)
        self.assertEqual(set(cookies.items()), set(json.load(open(TMP_FILE)).items()))

        # Test load cookies
        g = Grab(transport=GRAB_TRANSPORT)
        cookies = {'foo': 'bar', 'spam': u'бегемот'}
        json.dump(cookies, open(TMP_FILE, 'w'))
        g.load_cookies(TMP_FILE)
        self.assertEqual(set(g.config['cookies'].items()), set(cookies.items()))

    def test_cookiefile(self):
        g = Grab(transport=GRAB_TRANSPORT)

        # Empty file should not raise Exception
        open(TMP_FILE, 'w').write('')
        g.setup(cookiefile=TMP_FILE)
        g.go(BASE_URL)

        cookies = {'spam': 'ham'}
        json.dump(cookies, open(TMP_FILE, 'w'))

        # One cookie are sent in server reponse
        # Another cookies is passed via the `cookiefile` option
        RESPONSE['cookies'] = {'godzilla': 'monkey'}
        g.setup(cookiefile=TMP_FILE)
        g.go(BASE_URL)
        self.assertEqual(REQUEST['headers']['Cookie'], 'spam=ham')

        # This is correct reslt of combining two cookies
        MERGED_COOKIES = {'godzilla': 'monkey', 'spam': 'ham'}

        # g.config should contains merged cookies
        self.assertEqual(set(MERGED_COOKIES.items()),
                         set(g.config['cookies'].items()))

        # `cookiefile` file should contains merged cookies
        self.assertEqual(set(MERGED_COOKIES.items()),
                         set(json.load(open(TMP_FILE)).items()))
