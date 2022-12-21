from test_server import Response

from tests.util import BaseGrabTestCase, build_grab


class GrabSimpleTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_default_user_agent_is_not_random(self):
        self.server.add_response(Response())
        grab = build_grab()
        agents = set()
        for _ in range(3):
            grab.go(self.server.get_url())
            agents.add(self.server.request.headers.get("user-agent"))
        self.assertTrue(len(agents) == 1)

    def test_default_user_agent_is_diff_in_multi_grab_instances(self):
        self.server.add_response(Response(), count=-1)
        agents = set()
        for _ in range(3):
            grab = build_grab()
            grab.go(self.server.get_url())
            agents.add(self.server.request.headers.get("user-agent"))
        self.assertTrue(len(agents) > 1)
