# coding: utf-8
from unittest import TestCase
import string

from grab import Grab, GrabMisuseError
from util import (FakeServerThread, BASE_URL, RESPONSE, REQUEST,
                  RESPONSE_ONCE_HEADERS)

class TestCookies(TestCase):
    def setUp(self):
        FakeServerThread().start()

    def test_cookies_parsing(self):
        g = Grab()
        RESPONSE['cookies'] = {'foo': 'bar', '1': '2'}
        g.go(BASE_URL)
        self.assertEqual(g.response.cookies['foo'], 'bar')

    def test_multiple_cookies(self):
        g = Grab()
        RESPONSE['cookies'] = {}
        g.setup(cookies={'foo': '1', 'bar': '2'})
        g.go(BASE_URL)
        self.assertEqual(
            set(map(string.strip, REQUEST['headers']['Cookie'].split('; '))),
            set(['foo=1', 'bar=2']))

    def test_session(self):
        g = Grab()
        g.setup(reuse_cookies=True)
        RESPONSE['cookies'] = {'foo': 'bar'}
        g.go(BASE_URL)
        self.assertEqual(g.response.cookies['foo'], 'bar')
        g.go(BASE_URL)
        self.assertEqual(REQUEST['headers']['Cookie'], 'foo=bar')
        g.go(BASE_URL)
        self.assertEqual(REQUEST['headers']['Cookie'], 'foo=bar')

        g = Grab()
        g.setup(reuse_cookies=False)
        RESPONSE['cookies'] = {'foo': 'baz'}
        g.go(BASE_URL)
        self.assertEqual(g.response.cookies['foo'], 'baz')
        g.go(BASE_URL)
        self.assertTrue('Cookie' not in REQUEST['headers'])

        g = Grab()
        g.setup(reuse_cookies=True)
        RESPONSE['cookies'] = {'foo': 'bar'}
        g.go(BASE_URL)
        self.assertEqual(g.response.cookies['foo'], 'bar')
        g.clear_cookies()
        g.go(BASE_URL)
        self.assertTrue('Cookie' not in REQUEST['headers'])

    def test_redirect_session(self):
        g = Grab()
        RESPONSE['cookies'] = {'foo': 'bar'}
        g.go(BASE_URL)
        self.assertEqual(g.response.cookies['foo'], 'bar')

        # Setup one-time redirect
        g = Grab()
        RESPONSE['cookies'] = {}
        RESPONSE_ONCE_HEADERS.append(('Location', BASE_URL))
        RESPONSE_ONCE_HEADERS.append(('Set-Cookie', 'foo=bar'))
        RESPONSE['once_code'] = 302
        g.go(BASE_URL)
        self.assertEqual(REQUEST['headers']['Cookie'], 'foo=bar')
