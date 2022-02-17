from pprint import pprint
import time
from urllib.parse import quote

from tests.util import build_grab
from tests.util import BaseGrabTestCase


class TestCookies(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()
