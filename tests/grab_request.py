from pprint import pprint  # pylint: disable=unused-import

from test_server import Response

# from grab.error import (
#    GrabInternalError,
#    GrabCouldNotResolveHostError,
#    GrabTimeoutError,
#    GrabInvalidUrl,
# )

from tests.util import build_grab
from tests.util import BaseGrabTestCase


class GrabRequestTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_get_method(self):
        self.server.add_response(Response())
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertEqual("GET", self.server.request.method)

    def test_delete_method(self):
        self.server.add_response(Response())
        grab = build_grab()
        grab.setup(method="delete")
        grab.go(self.server.get_url())
        self.assertEqual("DELETE", self.server.request.method)

    def test_put_method(self):
        self.server.add_response(Response())
        grab = build_grab()
        grab.setup(method="put", post=b"abc")
        grab.go(self.server.get_url())
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
        grab.go(self.server.get_url())

    # def test_redirect_with_invalid_byte(self):
    #    url = self.server.get_url()
    #    invalid_url = "http://\xa0" + url  # .encode('ascii')

    #    def callback():
    #        return {
    #            "type": "response",
    #            "status": 301,
    #            "headers": [("Location", invalid_url)],
    #            "data": b"",
    #        }

    #    self.server.add_response(Response(callback=callback))
    #    grab = build_grab()
    #    # GrabTimeoutError raised when tests are being ran on computer
    #    # without access to the internet (no DNS service available)
    #    self.assertRaises(
    #        (
    #            GrabInternalError,
    #            GrabCouldNotResolveHostError,
    #            GrabTimeoutError,
    #            GrabInvalidUrl,
    #        ),
    #        grab.go,
    #        self.server.get_url(),
    #    )

    def test_options_method(self):
        self.server.add_response(Response())
        grab = build_grab()
        grab.setup(method="options", post=b"abc")
        grab.go(self.server.get_url())
        self.assertEqual("OPTIONS", self.server.request.method)
        self.assertEqual("3", self.server.request.headers.get("content-length"))

        self.server.add_response(Response())
        grab = build_grab()
        grab.setup(method="options")
        grab.go(self.server.get_url())
        self.assertEqual("OPTIONS", self.server.request.method)
        self.assertTrue("Content-Length" not in self.server.request.headers)
