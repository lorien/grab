from pprint import pprint  # pylint: disable=unused-import

from test_server import Response

from tests.util import BaseGrabTestCase, build_grab


class GrabRequestTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_get_method(self):
        self.server.add_response(Response())
        grab = build_grab()
        grab.request(self.server.get_url())
        self.assertEqual("GET", self.server.request.method)

    def test_delete_method(self):
        self.server.add_response(Response())
        grab = build_grab()
        grab.request(self.server.get_url(), method="DELETE")
        self.assertEqual("DELETE", self.server.request.method)

    def test_put_method(self):
        self.server.add_response(Response())
        grab = build_grab()
        grab.request(self.server.get_url(), method="PUT", body=b"abc")
        self.assertEqual("PUT", self.server.request.method)
        self.assertEqual("3", self.server.request.headers.get("content-length"))

    def test_head_with_invalid_bytes(self):
        def callback():
            return {
                "type": "response",
                "status": 200,
                "headers": [("Hello-Bug", b"start\xa0end")],
                "data": b"",
            }

        self.server.add_response(Response(callback=callback))
        grab = build_grab()
        grab.request(self.server.get_url())

    # def test_options_method(self):
    #    self.server.add_response(Response())
    #    grab = build_grab()
    #    grab.setup(method="OPTIONS")
    #    grab.request(self.server.get_url())
    #    self.assertEqual("OPTIONS", self.server.request.method)
    #    self.assertEqual("3", self.server.request.headers.get("content-length"))

    #    self.server.add_response(Response())
    #    grab = build_grab()
    #    grab.setup(method="OPTIONS")
    #    grab.request(self.server.get_url())
    #    self.assertEqual("OPTIONS", self.server.request.method)
    #    self.assertTrue("Content-Length" not in self.server.request.headers)
