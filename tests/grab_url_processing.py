# coding: utf-8
from tests.util import build_grab
from tests.util import BaseGrabTestCase


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
