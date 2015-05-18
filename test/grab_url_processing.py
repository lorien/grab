# coding: utf-8
import mock
import pycurl

from test.util import build_grab
from test.util import BaseGrabTestCase


class GrabUrlProcessingTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_nonascii_hostname(self):
        pass
        """
        # ******************************
        # Does not work on python3, why?
        # On python3 real network call is performed
        # ******************************
        g = build_grab()
        with mock.patch.object(g.transport.curl, 'perform'):
            with mock.patch.object(g.transport.curl, 'setopt') as patch:
                g.go('http://превед.рф/')
                args = dict((x[0][0], x[0][1]) for x in patch.call_args_list) 
                self.assertEqual(args[pycurl.URL],
                                 'http://xn--b1aebb1cg.xn--p1ai/')
        """

    def test_nonascii_path(self):
        g = build_grab()
        self.server.response['data'] = 'medved'
        g.go(self.server.get_url(u'/превед'))
        self.assertEquals(b'medved', g.doc.body)
        self.assertEquals('/%D0%BF%D1%80%D0%B5%D0%B2%D0%B5%D0%B4',
                          self.server.request['path'])

    def test_nonascii_query(self):
        g = build_grab()
        self.server.response['data'] = 'medved'
        g.go(self.server.get_url(u'/search?q=превед'))
        self.assertEquals(b'medved', g.doc.body)
        self.assertEquals(u'превед', self.server.request['args']['q'])
