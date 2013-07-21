# coding: utf-8
from unittest import TestCase

from grab import Grab, GrabMisuseError
from .util import GRAB_TRANSPORT, ignore_transport, only_transport
from .tornado_util import SERVER


class GrabSimpleTestCase(TestCase):
    def setUp(self):
        SERVER.reset()

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
        # For some transports it just allow them to send default user-agent
        # like in Kit transport case
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
