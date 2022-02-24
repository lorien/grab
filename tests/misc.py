from pprint import pprint  # pylint: disable=unused-import

from test_server import Response

from tests.util import build_grab  # pylint: disable=unused-import
from tests.util import BaseGrabTestCase, only_grab_transport


class TestMisc(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_put(self):
        pass

    # @only_grab_transport("pycurl")
    # def test_different_domains(self):
    #    import pycurl  # pylint: disable=import-outside-toplevel

    #    grab = build_grab()
    #    names = [
    #        "foo:%d:127.0.0.1" % self.server.port,
    #        "bar:%d:127.0.0.1" % self.server.port,
    #    ]
    #    grab.setup_transport("pycurl")
    #    grab.transport.curl.setopt(pycurl.RESOLVE, names)

    #    self.server.add_response(Response(headers=[("Set-Cookie", "foo=foo")]))
    #    grab.go("http://foo:%d" % self.server.port)
    #    self.assertEqual(dict(grab.doc.cookies.items()), {"foo": "foo"})

    #    self.server.add_response(Response(headers=[("Set-Cookie", "bar=bar")]))
    #    grab.go("http://bar:%d" % self.server.port)
    #    self.assertEqual(dict(grab.doc.cookies.items()), {"bar": "bar"})

    #    # That does not hold anymore, I guess I have fixed it
    #    # # response.cookies contains cookies from both domains
    #    # # because it just accumulates cookies over time
    #    # # self.assertEqual(
    #    # #     dict(grab.doc.cookies.items()), {"foo": "foo", "bar": "bar"}
    #    # # )
