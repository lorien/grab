from unittest import TestCase

from grab.request import HttpRequest
from grab.util.timeout import Timeout


class HttpRequestTestCase(TestCase):
    def test_constructor_timeout_not_specified(self) -> None:
        req = HttpRequest("https://example.com")
        self.assertTrue(isinstance(req.timeout, Timeout))

    def test_constructor_timeout_not_specified_default_values(self) -> None:
        req = HttpRequest("https://example.com")
        self.assertEqual(req.timeout.total, None)
        self.assertEqual(req.timeout.read, None)
        self.assertEqual(req.timeout.connect, None)

    def test_constructor_timeout_integer(self) -> None:
        req = HttpRequest("https://example.com", timeout=3)
        self.assertEqual(req.timeout.total, 3)
        self.assertEqual(req.timeout.read, 3)
        self.assertEqual(req.timeout.connect, 3)

    def test_constructor_timeout_object(self) -> None:
        req = HttpRequest("https://example.com", timeout=Timeout(total=4))
        self.assertEqual(req.timeout.total, 4)
        self.assertEqual(req.timeout.read, 4)
        self.assertEqual(req.timeout.connect, 4)
