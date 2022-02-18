from pprint import pprint  # pylint: disable=unused-import

from tests.util import build_grab  # pylint: disable=unused-import
from tests.util import BaseGrabTestCase


class TestCookies(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()
