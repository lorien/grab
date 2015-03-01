# coding: utf-8
from unittest import TestCase

from test.util import build_grab
from test.server import SERVER


class GrabRequestTestCase(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_get_method(self):
        g = build_grab()
        g.go(SERVER.BASE_URL)
        self.assertEquals('GET', SERVER.REQUEST['method'])

    def test_delete_method(self):
        g = build_grab()
        g.setup(method='delete')
        g.go(SERVER.BASE_URL)
        self.assertEquals('DELETE', SERVER.REQUEST['method'])

    def test_put_method(self):
        g = build_grab()
        g.setup(method='put', post=b'')
        g.go(SERVER.BASE_URL)
        self.assertEquals('PUT', SERVER.REQUEST['method'])
