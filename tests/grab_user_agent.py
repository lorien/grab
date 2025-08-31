# coding: utf-8
from tests.util import build_grab, only_grab_transport
from tests.util import BaseGrabTestCase, temp_file


class GrabSimpleTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_default_random_user_agent(self):
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertTrue(
            self.server.request['headers'].get('user-agent')
            .startswith('Mozilla/5.0 '))

    @only_grab_transport('pycurl')
    def test_empty_useragent_pycurl(self):
        grab = build_grab()

        # Empty string disable default pycurl user-agent
        grab.setup(user_agent='')
        grab.go(self.server.get_url())
        self.assertEqual(self.server.request['headers']
                         .get('user-agent', ''), '')

    def test_useragent_simple(self):
        grab = build_grab()

        # Simple case: setup user agent manually
        grab.setup(user_agent='foo')
        grab.go(self.server.get_url())
        self.assertEqual(self.server.request['headers']['user-agent'], 'foo')

    def test_useragent(self):
        grab = build_grab()

        # Null value activates default random user-agent
        # For some transports it just allow them to send default user-agent
        # like in Kit transport case
        grab = build_grab()
        grab.setup(user_agent=None)
        grab.go(self.server.get_url())
        self.assertTrue(len(self.server.request['headers']) > 0)
        self.assertFalse('PycURL' in
                         self.server.request['headers']['user-agent'])

        # By default user_agent is None => random user agent is generated
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertTrue(len(self.server.request['headers']) > 0)
        self.assertFalse('PycURL' in
                         self.server.request['headers']['user-agent'])

        # Simple case: setup user agent manually
        grab.setup(user_agent='foo')
        grab.go(self.server.get_url())
        self.assertEqual(self.server.request['headers']['user-agent'], 'foo')

        with temp_file() as ua_file:
            # user agent from file should be loaded
            with open(ua_file, 'w') as out:
                out.write('GOD')
            grab.setup(user_agent=None, user_agent_file=ua_file)
            grab.go(self.server.get_url())
            self.assertEqual(self.server.request['headers']['user-agent'],
                             'GOD')

        with temp_file() as ua_file:
            # random user agent from file should be loaded
            with open(ua_file, 'w') as out:
                out.write('GOD1\nGOD2')
            grab.setup(user_agent=None, user_agent_file=ua_file)
            grab.go(self.server.get_url())
            self.assertTrue(self.server.request['headers']['user-agent']
                            in ('GOD1', 'GOD2'))
            agent = grab.config['user_agent']

        # User-agent should not change
        grab.go(self.server.get_url())
        self.assertEqual(self.server.request['headers']['user-agent'], agent)

        # User-agent should not change
        grab.go(self.server.get_url())
        self.assertEqual(self.server.request['headers']['user-agent'], agent)
