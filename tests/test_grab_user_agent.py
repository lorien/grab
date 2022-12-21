from test_server import Response

from tests.util import BaseGrabTestCase, build_grab


class GrabSimpleTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_default_random_user_agent(self):
        self.server.add_response(Response())
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertTrue(
            self.server.request.headers.get("user-agent").startswith("Mozilla/5.0 ")
        )

    def test_useragent_simple(self):
        self.server.add_response(Response())
        grab = build_grab()

        # Simple case: setup user agent manually
        grab.setup(user_agent="foo")
        grab.go(self.server.get_url())
        self.assertEqual(self.server.request.headers.get("user-agent"), "foo")

    def test_useragent(self):
        self.server.add_response(Response(), count=7)
        grab = build_grab()

        # Null value activates default random user-agent
        # For some transports it just allow them to send default user-agent
        # like in Kit transport case
        grab = build_grab()
        grab.setup(user_agent=None)
        grab.go(self.server.get_url())
        self.assertTrue(self.server.request.headers.count_keys() > 0)
        self.assertFalse("PycURL" in self.server.request.headers.get("user-agent"))

        # By default user_agent is None => random user agent is generated
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertTrue(self.server.request.headers.count_keys() > 0)
        self.assertFalse("PycURL" in self.server.request.headers.get("user-agent"))

        # Simple case: setup user agent manually
        grab.setup(user_agent="foo")
        grab.go(self.server.get_url())
        self.assertEqual(self.server.request.headers.get("user-agent"), "foo")
