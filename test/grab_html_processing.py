# coding: utf-8
from glob import glob

from test.util import build_grab
from test.util import BaseGrabTestCase


class GrabHTMLProcessingTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_parse_document(self):
        """
        Simple test that verifies Grab can
        parse HTML pages with emoji
        Trying to reproduce error from
        https://github.com/lorien/grab/issues/199
        """
        for fname in glob('test/files/dump/*.html'):
            print('Parsing %s document' % fname)
            g = build_grab()
            self.server.response['data'] = open(fname, 'rb').read()
            g.go(self.server.get_url())
            for elem in g.doc('//*'):
                elem.text()

    def test_parse_cleaned_document(self):
        """
        Same as test_parse_document
        but documents are cleared from emoji
        """

        import re
        re_emoji = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "]+", flags=re.UNICODE)

        for fname in glob('test/files/dump/*.html'):
            print('Parsing %s document' % fname)
            g = build_grab()
            data = open(fname, 'rb').read()
            data = re_emoji.sub('', data.decode('utf-8')).encode('utf-8')
            self.server.response['data'] = data
            g.go(self.server.get_url())
            for elem in g.doc('//*'):
                elem.text()
