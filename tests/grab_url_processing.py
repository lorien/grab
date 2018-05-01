# coding: utf-8
from six.moves.urllib.parse import quote

from tests.util import (
    build_grab, BaseGrabTestCase, only_grab_transport
)
from grab.error import GrabConnectionError


class GrabUrlProcessingTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    #def test_nonascii_hostname(self):
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
        self.server.response['data'] = 'medved'
        grab.go(self.server.get_url(u'/превед'))
        self.assertEqual(b'medved', grab.doc.body)
        self.assertEqual('/%D0%BF%D1%80%D0%B5%D0%B2%D0%B5%D0%B4',
                         self.server.request['path'])

    def test_nonascii_query(self):
        grab = build_grab()
        self.server.response['data'] = 'medved'
        grab.go(self.server.get_url(u'/search?q=превед'))
        self.assertEqual(b'medved', grab.doc.body)
        self.assertEqual(u'превед', self.server.request['args']['q'])

    def test_null_byte_url(self):
        self.server.response_once['code'] = 302
        self.server.response_once['data'] = 'x'
        self.server.response['data'] = 'y'
        redirect_url = self.server.get_url().rstrip('/') + '/\x00/'
        self.server.response_once['headers'] = [
            ('Location', redirect_url)
        ]
        grab = build_grab()
        grab.go(self.server.get_url())
        self.assertEqual(b'y', grab.doc.body)
        self.assertEqual(grab.doc.url, quote(redirect_url, safe=':./?&'))

    @only_grab_transport('urllib3')
    def test_urllib3_idna_error(self):
        invalid_url = (
            'http://13354&altProductId=6423589&productId=6423589'
            '&altProductStoreId=13713&catalogId=10001'
            '&categoryId=28678&productStoreId=13713'
            'http://www.textbooksnow.com/webapp/wcs/stores'
            '/servlet/ProductDisplay?langId=-1&storeId='
        )
        grab = build_grab(transport='urllib3')
        with self.assertRaises(GrabConnectionError):
            grab.go(invalid_url)
