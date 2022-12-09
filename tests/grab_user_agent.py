from test_server import Response

from tests.util import BaseGrabTestCase, build_grab, temp_file


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

        with temp_file() as ua_file:
            # user agent from file should be loaded
            with open(ua_file, "w", encoding="utf-8") as out:
                out.write("GOD")
            grab.setup(user_agent=None, user_agent_file=ua_file)
            grab.go(self.server.get_url())
            self.assertEqual(self.server.request.headers.get("user-agent"), "GOD")

        with temp_file() as ua_file:
            # random user agent from file should be loaded
            with open(ua_file, "w", encoding="utf-8") as out:
                out.write("GOD1\nGOD2")
            grab.setup(user_agent=None, user_agent_file=ua_file)
            grab.go(self.server.get_url())
            self.assertTrue(
                self.server.request.headers.get("user-agent") in ("GOD1", "GOD2")
            )
            agent = grab.config["user_agent"]

        # User-agent should not change
        grab.go(self.server.get_url())
        self.assertEqual(self.server.request.headers.get("user-agent"), agent)

        # User-agent should not change
        grab.go(self.server.get_url())
        self.assertEqual(self.server.request.headers.get("user-agent"), agent)
