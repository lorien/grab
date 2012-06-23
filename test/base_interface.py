# coding: utf-8
from unittest import TestCase

from grab import Grab, GrabMisuseError
from util import (FakeServerThread, BASE_URL, RESPONSE, REQUEST,
                  RESPONSE_ONCE, ignore_transport, GRAB_TRANSPORT,
                  ignore_transport, only_transport)

class TestGrab(TestCase):
    def setUp(self):
        FakeServerThread().start()

    #def test_basic(self):
        #RESPONSE['get'] = '<meta charset="utf-8">The cat is кошка'
        #g = Grab(transport=GRAB_TRANSPORT)
        #g.go(BASE_URL)
        #self.assertTrue('The cat' in g.response.body)
        #self.assertTrue('кошка' in g.response.body)

    def test_xml_with_declaration(self):
        RESPONSE['get'] = '<?xml version="1.0" encoding="UTF-8"?><root><foo>foo</foo></root>'
        g = Grab(strip_xml_declaration=True, transport=GRAB_TRANSPORT)
        g.go(BASE_URL)
        self.assertTrue(g.xpath('//foo').text == 'foo')

    def test_incorrect_option_name(self):
        g = Grab(transport=GRAB_TRANSPORT)
        self.assertRaises(GrabMisuseError,
            lambda: g.setup(save_the_word=True))

    @only_transport('curl.CurlTransport')
    def test_empty_useragent_pycurl(self):
        g = Grab(transport=GRAB_TRANSPORT)

        # Empty string disable default pycurl user-agent
        g.setup(user_agent='')
        g.go(BASE_URL)
        self.assertEqual(REQUEST['headers'].get('user-agent', ''), '')

    @ignore_transport('ghost.GhostTransport')
    def test_useragent_simple(self):
        g = Grab(transport=GRAB_TRANSPORT)

        # Simple case: setup user agent manually
        g.setup(user_agent='foo')
        g.go(BASE_URL)
        self.assertEqual(REQUEST['headers']['user-agent'], 'foo')

    @ignore_transport('ghost.GhostTransport')
    def test_useragent(self):
        g = Grab(transport=GRAB_TRANSPORT)

        # Null value activates default random user-agent
        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(user_agent=None)
        g.go(BASE_URL)
        self.assertTrue(len(REQUEST['headers']) > 0)
        self.assertFalse('PycURL' in REQUEST['headers']['user-agent'])

        # By default user_agent is None => random user agent is generated
        g = Grab(transport=GRAB_TRANSPORT)
        g.go(BASE_URL)
        self.assertTrue(len(REQUEST['headers']) > 0)
        self.assertFalse('PycURL' in REQUEST['headers']['user-agent'])

        # Simple case: setup user agent manually
        g.setup(user_agent='foo')
        g.go(BASE_URL)
        self.assertEqual(REQUEST['headers']['user-agent'], 'foo')
        
        # user agent from file should be loaded
        path = '/tmp/__ua.txt'
        open(path, 'w').write('GOD')
        g.setup(user_agent=None, user_agent_file=path)
        g.go(BASE_URL)
        self.assertEqual(REQUEST['headers']['user-agent'], 'GOD')

        # random user agent from file should be loaded
        path = '/tmp/__ua.txt'
        open(path, 'w').write('GOD1\nGOD2')
        g.setup(user_agent=None, user_agent_file=path)
        g.go(BASE_URL)
        self.assertTrue(REQUEST['headers']['user-agent'] in ('GOD1', 'GOD2'))
        ua = g.config['user_agent']

        # User-agent should not change
        g.go(BASE_URL)
        self.assertEqual(REQUEST['headers']['user-agent'], ua)

        # User-agent should not change
        g.go(BASE_URL)
        self.assertEqual(REQUEST['headers']['user-agent'], ua)

    def test_clone(self):
        g = Grab(transport=GRAB_TRANSPORT)
        RESPONSE['get'] = 'Moon'
        g.go(BASE_URL)
        self.assertTrue('Moon' in g.response.body)
        g2 = Grab(transport=GRAB_TRANSPORT)
        self.assertEqual(g2.response, None)
        g2 = g.clone()
        self.assertTrue('Moon' in g.response.body)

    def test_empty_clone(self):
        g = Grab()
        g.clone()

    def test_adopt(self):
        g = Grab(transport=GRAB_TRANSPORT)
        RESPONSE['get'] = 'Moon'
        g.go(BASE_URL)
        g2 = Grab(transport=GRAB_TRANSPORT)
        self.assertEqual(g2.config['url'], None)
        g2.adopt(g)
        self.assertTrue('Moon' in g2.response.body)
        self.assertEqual(g2.config['url'], BASE_URL)

    def test_empty_adopt(self):
        g = Grab()
        g2 = Grab()
        g2.adopt(g)

    def test_find_content_blocks(self):
        porno = u'порно ' * 100
        redis = u'редис ' * 100
        RESPONSE['get'] = ('<div>%s</div><p>%s' % (porno, redis)).encode('utf-8')
        g = Grab(transport=GRAB_TRANSPORT)
        g.go(BASE_URL)
        blocks = list(g.find_content_blocks())
        print '>>>'
        print blocks[0]
        print '<<<'
        print ')))'
        print porno.strip()
        print '((('
        self.assertEqual(blocks[0], porno.strip())
        #self.assertEqual(blocks[1], redis.strip())

    def test_meta_refresh_redirect(self):
        # By default meta-redirect is off
        url = BASE_URL + '/foo'
        RESPONSE_ONCE['get'] = '<meta http-equiv="refresh" content="5; url=%s">' % url
        g = Grab(transport=GRAB_TRANSPORT)
        g.go(BASE_URL + '/')
        self.assertEqual(REQUEST['path'], '/')
        self.assertEqual(g.response.url, BASE_URL + '/')

        # Now test meta-auto-redirect
        RESPONSE_ONCE['get'] = '<meta http-equiv="refresh" content="5; url=%s">' % url
        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(follow_refresh=True)
        g.go(BASE_URL)
        self.assertEqual(REQUEST['path'], '/foo')
        self.assertEqual(g.response.url, BASE_URL + '/foo')

    @only_transport('curl.CurlTransport')
    def test_redirect_limit(self):

        class Scope(object):
            counter = None

            def callback(self, server):
                if self.counter:
                    server.send_response(301)
                    server.send_header('Location', BASE_URL)
                    server.end_headers()
                else:
                    server.send_response(200)
                    server.end_headers()
                self.counter -= 1

        scope = Scope()
        scope.counter = 10
        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(redirect_limit=5)

        RESPONSE['get_callback'] = scope.callback

        try:
            try:
                g.go(BASE_URL)
            except Exception, ex:
                pass
            self.assert_(ex is not None)
            self.assertEqual(ex.errno, 47)

            scope.counter = 10
            g.setup(redirect_limit=20)

            try:
                g.go(BASE_URL)
            except Exception, ex:
                pass
            else:
                ex = None
            self.assert_(ex is None)

        finally:
            # Clean up test environment
            RESPONSE['get_callback'] = None

    def test_default_content_for_fake_response(self):
        content = '<strong>test</strong>'
        g = Grab(content)
        self.assertEqual(g.response.body, content)

    # TODO: move into test/bugs.py
    def test_declaration_bug(self):
        """
        1. Build Grab instance with XML with xml declaration
        2. Call search method
        3. Call xpath
        4. Get ValueError: Unicode strings with encoding declaration are not supported.
        """
        xml = '<?xml version="1.0" encoding="UTF-8"?><tree><leaf>text</leaf></tree>'
        g = Grab(xml)
        self.assertTrue(g.search(u'text'))
        self.assertEqual(g.xpath('//leaf').text, u'text')

        # Similar bugs
        g = Grab(xml)
        self.assertTrue(g.rex(u'text'))
        self.assertEqual(g.xpath('//leaf').text, u'text')
