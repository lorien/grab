from unittest import TestCase

from grab import Grab
from grab.transport.mock import GrabMockNotFoundError, MOCK_REGISTRY
from .tornado_util import SERVER

MOCK_TRANSPORT = 'grab.transport.mock.MockTransport'

class GrabTransortMockTestCase(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_integrity(self):
        g = Grab(transport=MOCK_TRANSPORT)

    def test_missed_url(self):
        g = Grab(transport=MOCK_TRANSPORT)
        self.assertRaises(GrabMockNotFoundError,
                          lambda: g.go('http://yandex.ru'))

    def test_registry(self):
        g = Grab(transport=MOCK_TRANSPORT)
        MOCK_REGISTRY['http://yandex.ru/'] = 'foo'
        g.go('http://yandex.ru/')
        self.assertEqual(g.response.body, 'foo')
        self.assertEqual(g.response.code, 200)
