from test_server import Response

from grab.error import GrabInvalidResponse, GrabTooManyRedirectsError
from tests.util import BaseGrabTestCase, build_grab


def build_location_callback(url, counter):
    meta = {
        "counter": counter,
        "url": url,
    }

    def callback():
        if meta["counter"]:
            status = 301
            headers = [("Location", meta["url"])]
            data = b""
        else:
            status = 200
            headers = []
            data = b"done"
        meta["counter"] -= 1
        return {
            "type": "response",
            "status": status,
            "data": data,
            "headers": headers,
        }

    return callback


class GrabRedirectTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_redirect_limit(self):
        self.server.add_response(
            Response(callback=build_location_callback(self.server.get_url(), 10)),
            count=-1,
        )

        grab = build_grab()
        grab.setup(redirect_limit=5)

        self.assertRaises(
            GrabTooManyRedirectsError, lambda: grab.request(self.server.get_url())
        )

        self.server.add_response(
            Response(callback=build_location_callback(self.server.get_url(), 10)),
            count=-1,
        )
        grab.setup(redirect_limit=20)
        grab.request(self.server.get_url())
        self.assertTrue(b"done" in grab.doc.body)

    def test_redirect_utf_location(self):
        def callback():
            url = (self.server.get_url() + "фыва").encode("utf-8")
            return (
                b"HTTP/1.1 301 OK\nLocation: %s\nLocation-Length: 9\n\ncontent-1" % url
            )

        self.server.add_response(Response(raw_callback=callback))
        self.server.add_response(Response(data=b"content-2"))
        grab = build_grab(follow_location=True)
        with self.assertRaises(GrabInvalidResponse):
            grab.request(self.server.get_url())
