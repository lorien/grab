# coding: utf-8
from unittest import TestCase
#import string
import json

from grab import Grab, GrabMisuseError
from .util import TMP_FILE, GRAB_TRANSPORT
from .tornado_util import SERVER

class TestCookies(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_parsing_response_cookies(self):
        g = Grab(transport=GRAB_TRANSPORT)
        SERVER.RESPONSE['cookies'] = {'foo': 'bar', '1': '2'}
        g.go(SERVER.BASE_URL)
        self.assertEqual(g.response.cookies['foo'], 'bar')

    def test_multiple_cookies(self):
        g = Grab(transport=GRAB_TRANSPORT)
        SERVER.RESPONSE['cookies'] = {}
        g.setup(cookies={'foo': '1', 'bar': '2'})
        g.go(SERVER.BASE_URL)
        self.assertEqual(
            set(map(lambda item: item.strip(),
                    SERVER.REQUEST['headers']['Cookie'].split('; '))),
            set(['foo=1', 'bar=2']))

    def test_session(self):
        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(reuse_cookies=True)
        SERVER.RESPONSE['cookies'] = {'foo': 'bar'}
        g.go(SERVER.BASE_URL)
        self.assertEqual(g.response.cookies['foo'], 'bar')
        g.go(SERVER.BASE_URL)
        self.assertEqual(SERVER.REQUEST['headers']['Cookie'], 'foo=bar')
        g.go(SERVER.BASE_URL)
        self.assertEqual(SERVER.REQUEST['headers']['Cookie'], 'foo=bar')

        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(reuse_cookies=False)
        SERVER.RESPONSE['cookies'] = {'foo': 'baz'}
        g.go(SERVER.BASE_URL)
        self.assertEqual(g.response.cookies['foo'], 'baz')
        g.go(SERVER.BASE_URL)
        self.assertTrue('Cookie' not in SERVER.REQUEST['headers'])

        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(reuse_cookies=True)
        SERVER.RESPONSE['cookies'] = {'foo': 'bar'}
        g.go(SERVER.BASE_URL)
        self.assertEqual(g.response.cookies['foo'], 'bar')
        g.clear_cookies()
        g.go(SERVER.BASE_URL)
        self.assertTrue('Cookie' not in SERVER.REQUEST['headers'])

    def test_redirect_session(self):
        g = Grab(transport=GRAB_TRANSPORT)
        SERVER.RESPONSE['cookies'] = {'foo': 'bar'}
        g.go(SERVER.BASE_URL)
        self.assertEqual(g.response.cookies['foo'], 'bar')

        # Setup one-time redirect
        g = Grab(transport=GRAB_TRANSPORT)
        SERVER.RESPONSE['cookies'] = {}
        SERVER.RESPONSE_ONCE['headers'].append(('Location', SERVER.BASE_URL))
        SERVER.RESPONSE_ONCE['headers'].append(('Set-Cookie', 'foo=bar'))
        SERVER.RESPONSE_ONCE['code'] = 302
        g.go(SERVER.BASE_URL)
        self.assertEqual(SERVER.REQUEST['headers']['Cookie'], 'foo=bar')

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
        g.go(SERVER.BASE_URL)

        cookies = {'spam': 'ham'}
        json.dump(cookies, open(TMP_FILE, 'w'))

        # One cookie are sent in server reponse
        # Another cookies is passed via the `cookiefile` option
        SERVER.RESPONSE['cookies'] = {'godzilla': 'monkey'}
        g.setup(cookiefile=TMP_FILE)
        g.go(SERVER.BASE_URL)
        self.assertEqual(SERVER.REQUEST['headers']['Cookie'], 'spam=ham')

        # This is correct reslt of combining two cookies
        MERGED_COOKIES = {'godzilla': 'monkey', 'spam': 'ham'}

        # g.config should contains merged cookies
        self.assertEqual(set(MERGED_COOKIES.items()),
                         set(g.config['cookies'].items()))

        # `cookiefile` file should contains merged cookies
        self.assertEqual(set(MERGED_COOKIES.items()),
                         set(json.load(open(TMP_FILE)).items()))
