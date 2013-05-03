# coding: utf-8
from unittest import TestCase
import os

from grab import Grab, GrabMisuseError
from util import (GRAB_TRANSPORT, TMP_DIR,
                  ignore_transport, only_transport)
from tornado_util import SERVER
from grab.extension import register_extensions


class TestGrab(TestCase):
    def setUp(self):
        SERVER.reset()

    #def test_basic(self):
        #SERVER.RESPONSE['get'] = '<meta charset="utf-8">The cat is кошка'
        #g = Grab(transport=GRAB_TRANSPORT)
        #g.go(SERVER.BASE_URL)
        #self.assertTrue('The cat' in g.response.body)
        #self.assertTrue('кошка' in g.response.body)

    def test_xml_with_declaration(self):
        SERVER.RESPONSE['get'] = '<?xml version="1.0" encoding="UTF-8"?><root><foo>foo</foo></root>'
        g = Grab(strip_xml_declaration=True, transport=GRAB_TRANSPORT)
        g.go(SERVER.BASE_URL)
        self.assertTrue(g.xpath_one('//foo').text == 'foo')

    def test_incorrect_option_name(self):
        g = Grab(transport=GRAB_TRANSPORT)
        self.assertRaises(GrabMisuseError,
            lambda: g.setup(save_the_word=True))

    @only_transport('grab.transport.curl.CurlTransport')
    def test_empty_useragent_pycurl(self):
        g = Grab(transport=GRAB_TRANSPORT)

        # Empty string disable default pycurl user-agent
        g.setup(user_agent='')
        g.go(SERVER.BASE_URL)
        self.assertEqual(SERVER.REQUEST['headers'].get('user-agent', ''), '')

    @ignore_transport('ghost.GhostTransport')
    def test_useragent_simple(self):
        g = Grab(transport=GRAB_TRANSPORT)

        # Simple case: setup user agent manually
        g.setup(user_agent='foo')
        g.go(SERVER.BASE_URL)
        self.assertEqual(SERVER.REQUEST['headers']['user-agent'], 'foo')

    @ignore_transport('ghost.GhostTransport')
    def test_useragent(self):
        g = Grab(transport=GRAB_TRANSPORT)

        # Null value activates default random user-agent
        g = Grab(transport=GRAB_TRANSPORT)
        g.setup(user_agent=None)
        g.go(SERVER.BASE_URL)
        self.assertTrue(len(SERVER.REQUEST['headers']) > 0)
        self.assertFalse('PycURL' in SERVER.REQUEST['headers']['user-agent'])

        # By default user_agent is None => random user agent is generated
        g = Grab(transport=GRAB_TRANSPORT)
        g.go(SERVER.BASE_URL)
        self.assertTrue(len(SERVER.REQUEST['headers']) > 0)
        self.assertFalse('PycURL' in SERVER.REQUEST['headers']['user-agent'])

        # Simple case: setup user agent manually
        g.setup(user_agent='foo')
        g.go(SERVER.BASE_URL)
        self.assertEqual(SERVER.REQUEST['headers']['user-agent'], 'foo')
        
        # user agent from file should be loaded
        path = '/tmp/__ua.txt'
        open(path, 'w').write('GOD')
        g.setup(user_agent=None, user_agent_file=path)
        g.go(SERVER.BASE_URL)
        self.assertEqual(SERVER.REQUEST['headers']['user-agent'], 'GOD')

        # random user agent from file should be loaded
        path = '/tmp/__ua.txt'
        open(path, 'w').write('GOD1\nGOD2')
        g.setup(user_agent=None, user_agent_file=path)
        g.go(SERVER.BASE_URL)
        self.assertTrue(SERVER.REQUEST['headers']['user-agent'] in ('GOD1', 'GOD2'))
        ua = g.config['user_agent']

        # User-agent should not change
        g.go(SERVER.BASE_URL)
        self.assertEqual(SERVER.REQUEST['headers']['user-agent'], ua)

        # User-agent should not change
        g.go(SERVER.BASE_URL)
        self.assertEqual(SERVER.REQUEST['headers']['user-agent'], ua)

    @ignore_transport('ghost.GhostTransport')
    # Disabled because of strance error
    # Error when another Ghost instance is created
    def test_clone(self):
        g = Grab(transport=GRAB_TRANSPORT)
        SERVER.RESPONSE['get'] = 'Moon'
        g.go(SERVER.BASE_URL)
        self.assertTrue('Moon' in g.response.body)
        g2 = Grab(transport=GRAB_TRANSPORT)
        self.assertEqual(g2.response, None)
        g2 = g.clone()
        self.assertTrue('Moon' in g.response.body)

    @ignore_transport('ghost.GhostTransport')
    def test_empty_clone(self):
        g = Grab()
        g.clone()

    @ignore_transport('ghost.GhostTransport')
    def test_adopt(self):
        g = Grab(transport=GRAB_TRANSPORT)
        SERVER.RESPONSE['get'] = 'Moon'
        g.go(SERVER.BASE_URL)
        g2 = Grab(transport=GRAB_TRANSPORT)
        self.assertEqual(g2.config['url'], None)
        g2.adopt(g)
        self.assertTrue('Moon' in g2.response.body)
        self.assertEqual(g2.config['url'], SERVER.BASE_URL)

    def test_empty_adopt(self):
        g = Grab()
        g2 = Grab()
        g2.adopt(g)

    def test_find_content_blocks(self):
        # TODO: move to separate file
        from grab.tools.content import find_content_blocks
        porno = u'порно ' * 100
        redis = u'редис ' * 100
        SERVER.RESPONSE['get'] = ('<div>%s</div><p>%s' % (porno, redis)).encode('utf-8')
        g = Grab(transport=GRAB_TRANSPORT)
        g.go(SERVER.BASE_URL)
        blocks = list(find_content_blocks(g.tree))
        print '>>>'
        print blocks[0]
        print '<<<'
        print ')))'
        print porno.strip()
        print '((('
        self.assertEqual(blocks[0], porno.strip())
        #self.assertEqual(blocks[1], redis.strip())

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
        self.assertEqual(g.xpath_one('//leaf').text, u'text')

        # Similar bugs
        g = Grab(xml)
        self.assertTrue(g.rex(u'text'))
        self.assertEqual(g.xpath_one('//leaf').text, u'text')

    def test_inheritance(self):
        class SimpleExtension(object):
            data = {'counter': 0}

            def extra_init(self):
                self.get_data()['counter'] += 1

            @classmethod
            def get_data(cls):
                return cls.data

        class CustomGrab(Grab, SimpleExtension):
            pass

        register_extensions(CustomGrab)

        SimpleExtension.get_data()['counter'] = 0
        g = CustomGrab()
        self.assertEqual(SimpleExtension.get_data()['counter'], 1)

        class VeryCustomGrab(CustomGrab):
            pass

        SimpleExtension.get_data()['counter'] = 0
        g = VeryCustomGrab()
        self.assertEqual(SimpleExtension.get_data()['counter'], 1)


        # TODO: what did I mean? :)
        # Anyway it does not work now :)
        #class VeryCustomGrab(CustomGrab, SimpleExtension):
            #pass

        #SimpleExtension.get_data()['counter'] = 0
        #g = VeryCustomGrab()
        #self.assertEqual(SimpleExtension.get_data()['counter'], 2)

    def test_body_inmemory(self):
        g = Grab()
        g.setup(body_inmemory=False)
        self.assertRaises(GrabMisuseError, lambda: g.go(SERVER.BASE_URL))

        SERVER.RESPONSE['get'] = 'foo'
        g = Grab()
        g.setup(body_inmemory=False)
        g.setup(body_storage_dir=TMP_DIR)
        g.go(SERVER.BASE_URL)
        self.assertTrue(os.path.exists(g.response.body_path))
        self.assertTrue(TMP_DIR in g.response.body_path)
        self.assertEqual('foo', open(g.response.body_path).read())
        old_path = g.response.body_path

        g.go(SERVER.BASE_URL)
        self.assertTrue(old_path != g.response.body_path)

        SERVER.RESPONSE['get'] = 'foo'
        g = Grab()
        g.setup(body_inmemory=False)
        g.setup(body_storage_dir=TMP_DIR)
        g.setup(body_storage_filename='musik.mp3')
        g.go(SERVER.BASE_URL)
        self.assertTrue(os.path.exists(g.response.body_path))
        self.assertTrue(TMP_DIR in g.response.body_path)
        self.assertEqual('foo', open(g.response.body_path).read())
        self.assertEqual(os.path.join(TMP_DIR, 'musik.mp3'), g.response.body_path)
