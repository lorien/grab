# coding: utf-8
from glob import glob

from test.util import build_grab
from test.util import BaseGrabTestCase


class GrabHTMLProcessingTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_xml_with_declaration(self):
        """
        Simple test that verifies Grab can
        parse HTML pages with emoji
        Trying to reproduce error from
        https://github.com/lorien/grab/issues/199
        """
        for fname in glob('test/files/dump/*.html'):
            g = build_grab()
            self.server.response['data'] = open(fname, 'rb').read()
            g.go(self.server.get_url())
            for elem in g.doc('//*'):
                elem.text()
