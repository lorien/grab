from pprint import pprint  # pylint: disable=unused-import

from tests.util import BaseGrabTestCase


class TestMisc(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()
