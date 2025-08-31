# coding: utf-8
from tests.util import build_grab
from tests.util import BaseGrabTestCase


class GrabDocumentTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_document_copy_works(self):
        grab = build_grab()
        self.server.response['data'] = (
            b'<h1>test</h1>'
        )
        res1 = grab.go(self.server.get_url())
        self.assertEqual('test', res1.select('//h1').text())

        res2 = res1.copy()
        self.assertEqual('test', res2.select('//h1').text())
