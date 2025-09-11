# coding: utf-8
from pprint import pprint  # pylint: disable=unused-import # noqa: F401

from six.moves.urllib.parse import quote

from grab.error import GrabTooManyRedirectsError
from test_server import Request, Response
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
        res = {
            "type": "response",
            "status": status,
            "data": data,
            "headers": headers,
        }
        return res

    return callback


def build_refresh_callback(url, counter):
    meta = {
        "counter": counter,
        "url": url,
    }

    def callback():
        if meta["counter"]:
            status = 200
            data = b"<html><head><meta " b'http-equiv="refresh" content="5"></head>'
        else:
            status = 200
            data = b"done"
        meta["counter"] -= 1
        return {"type": "response", "status": status, "data": data}

    return callback


class GrabRedirectTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_follow_refresh_off(self):
       # By default meta-redirect is off
       meta_url = self.server.get_url("/foo")
       self.server.add_response(
           Response(data='<meta http-equiv="refresh" content="5; url=%s">' % meta_url),
           count=1,
       )
       grab = build_grab()
       grab.go(self.server.get_url())
       req = self.server.get_request()
       self.assertEqual(req.path, "/")
       self.assertEqual(grab.doc.url, self.server.get_url("/"))

    def test_follow_refresh_on(self):
       meta_url = self.server.get_url("/foo")
       # Now test meta-auto-redirect
       self.server.add_response(
           Response(data='<meta http-equiv="refresh" content="5; url=%s">' % meta_url),
           count=1,
       )
       self.server.add_response(Response())
       grab = build_grab()
       grab.setup(follow_refresh=True)
       grab.go(self.server.get_url())
       req = self.server.get_request()
       self.assertEqual(req.path, "/foo")
       self.assertEqual(grab.doc.url, meta_url)

    def test_spaces_in_refresh_url(self):
       meta_url = self.server.get_url("/foo")
       # Test spaces in meta tag
       self.server.add_response(
           Response(data="<meta http-equiv='refresh' content='0;url= %s'>" % meta_url),
           count=1,
           method="get",
       )
       self.server.add_response(Response(data="ok"))
       grab = build_grab()
       grab.setup(follow_refresh=True)
       grab.go(self.server.get_url())
       req = self.server.get_request()
       self.assertEqual(req.path, "/foo")
       self.assertEqual(grab.doc.url, meta_url)

    def test_refresh_redirect_limit(self):
       self.server.add_response(Response(callback=build_refresh_callback(
           self.server.get_url(), 10
       )), count=-1)

       grab = build_grab()
       grab.setup(redirect_limit=10, follow_refresh=True)
       grab.go(self.server.get_url())
       self.assertTrue(b"done" in grab.doc.body)

       self.server.add_response(Response(callback = build_refresh_callback(
           self.server.get_url(), 10
       )), count=-1)
       grab.setup(redirect_limit=5, follow_refresh=True)
       self.assertRaises(
           GrabTooManyRedirectsError, lambda: grab.go(self.server.get_url())
       )

    def test_redirect_limit(self):
        self.server.add_response(
            Response(callback=build_location_callback(self.server.get_url(), 10)),
            count=-1,
        )

        grab = build_grab()
        grab.setup(redirect_limit=5)

        with self.assertRaises(GrabTooManyRedirectsError):
            grab.go(self.server.get_url())

        self.server.add_response(Response(callback=build_location_callback(
            self.server.get_url(), 10
        )))
        grab.setup(redirect_limit=20)
        grab.go(self.server.get_url())
        self.assertTrue(b"done" in grab.doc.body)


    def test_redirect_utf_location(self):
       # fmt: off
       self.server.add_response(
           Response(
               status=301,
               headers=[
                   ("Location", (self.server.get_url() + u"/фыва").encode("utf-8")),
               ]
           ),
           count=1,
       )
       # fmt: on
       self.server.add_response(Response(), count=1)
       grab = build_grab(debug=True, follow_location=True)
       grab.go(self.server.get_url())
       # fmt: off
       self.assertTrue(quote(u"/фыва".encode("utf-8"), safe="/") in grab.doc.url)
       # fmt: on
