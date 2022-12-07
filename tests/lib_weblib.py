from weblib.http import normalize_url

from tests.util import BaseGrabTestCase


class GrabApiTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_normalize_url(self):
        url = b"http://\xa0http://localhost:7777/"
        with self.assertRaises(UnicodeDecodeError):
            normalize_url(url)
