# coding: utf-8
from six.moves.urllib.parse import quote

from grab.error import GrabConnectionError
from test_server import Request, Response
from tests.util import BaseGrabTestCase, build_grab, only_grab_transport


class GrabUrlProcessingTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    # def test_nonascii_hostname(self):
    #    #TODO: FIXME
    #    # ******************************
    #    # Does not work on python3, why?
    #    # On python3 real network call is performed
    #    # ******************************
    #    grab = build_grab()
    #    with mock.patch.object(grab.transport.curl, 'perform'):
    #        with mock.patch.object(grab.transport.curl, 'setopt') as patch:
    #            grab.go('http://превед.рф/')
    #            args = dict((x[0][0], x[0][1]) for x in patch.call_args_list)
    #            self.assertEqual(args[pycurl.URL],
    #                             'http://xn--b1aebb1cgrab.xn--p1ai/')

    def test_nonascii_path(self):
        grab = build_grab()
        self.server.add_response(Response(data="medved"), count=1)
        url = self.server.get_url("/превед?foo=bar")
        grab.go(url)
        self.assertEqual(b"medved", grab.doc.body)
        self.assertEqual(
            #'/%D0%BF%D1%80%D0%B5%D0%B2%D0%B5%D0%B4',
            "/превед",
            self.server.get_request().path,
        )

    def test_nonascii_query(self):
        grab = build_grab()
        self.server.add_response(Response(data="medved"), count=1)
        grab.go(self.server.get_url("/search?q=превед"))
        self.assertEqual(b"medved", grab.doc.body)
        req = self.server.get_request()
        self.assertEqual("превед", req.args["q"])

    def test_null_byte_url(self):
        redirect_url = self.server.get_url().rstrip("/") + "/\x00/"
        self.server.add_response(
            Response(status=302, data="x", headers=[("Location", redirect_url)]),
            count=1,
        )
        self.server.add_response(Response(data="y"), count=1)
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertEqual(b"y", grab.doc.body)
        self.assertEqual(grab.doc.url, quote(redirect_url, safe=":./?&"))

    @only_grab_transport("urllib3")
    def test_urllib3_idna_error(self):
        invalid_url = (
            "http://13354&altProductId=6423589&productId=6423589"
            "&altProductStoreId=13713&catalogId=10001"
            "&categoryId=28678&productStoreId=13713"
            "http://www.textbooksnow.com/webapp/wcs/stores"
            "/servlet/ProductDisplay?langId=-1&storeId="
        )
        grab = build_grab(transport="urllib3")
        with self.assertRaises(GrabConnectionError):
            grab.go(invalid_url)
