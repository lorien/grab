# coding: utf-8
from test.util import build_grab
from test.util import BaseGrabTestCase


class GrabSimpleTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_empty_useragent_pycurl(self):
        g = build_grab()

        # Empty string disable default pycurl user-agent
        g.setup(user_agent='')
        g.go(self.server.get_url())
        self.assertEqual(self.server.request['headers']
                             .get('user-agent', ''), '')

    def test_useragent_simple(self):
        g = build_grab()

        # Simple case: setup user agent manually
        g.setup(user_agent='foo')
        g.go(self.server.get_url())
        self.assertEqual(self.server.request['headers']['user-agent'], 'foo')

    def test_useragent(self):
        g = build_grab()

        # Null value activates default random user-agent
        # For some transports it just allow them to send default user-agent
        # like in Kit transport case
        g = build_grab()
        g.setup(user_agent=None)
        g.go(self.server.get_url())
        self.assertTrue(len(self.server.request['headers']) > 0)
        self.assertFalse('PycURL' in
                         self.server.request['headers']['user-agent'])

        # By default user_agent is None => random user agent is generated
        g = build_grab()
        g.go(self.server.get_url())
        self.assertTrue(len(self.server.request['headers']) > 0)
        self.assertFalse('PycURL' in
                         self.server.request['headers']['user-agent'])

        # Simple case: setup user agent manually
        g.setup(user_agent='foo')
        g.go(self.server.get_url())
        self.assertEqual(self.server.request['headers']['user-agent'], 'foo')

        # user agent from file should be loaded
        path = '/tmp/__ua.txt'
        open(path, 'w').write('GOD')
        g.setup(user_agent=None, user_agent_file=path)
        g.go(self.server.get_url())
        self.assertEqual(self.server.request['headers']['user-agent'], 'GOD')

        # random user agent from file should be loaded
        path = '/tmp/__ua.txt'
        open(path, 'w').write('GOD1\nGOD2')
        g.setup(user_agent=None, user_agent_file=path)
        g.go(self.server.get_url())
        self.assertTrue(self.server.request['headers']['user-agent']
                        in ('GOD1', 'GOD2'))
        ua = g.config['user_agent']

        # User-agent should not change
        g.go(self.server.get_url())
        self.assertEqual(self.server.request['headers']['user-agent'], ua)

        # User-agent should not change
        g.go(self.server.get_url())
        self.assertEqual(self.server.request['headers']['user-agent'], ua)
