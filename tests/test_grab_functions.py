from unittest import TestCase

from grab import Grab, request
from grab.document import Document


class RequestFuncTestCase(TestCase):
    def test_request_custom_grab(self):
        class DummyDocument(Document):
            pass

        class DummyGrab(Grab):
            def request(self, *_args, **_kwargs):
                return DummyDocument()

        self.assertTrue(
            isinstance(request("http://example.com", grab=DummyGrab), DummyDocument)
        )
