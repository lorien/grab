# coding: utf-8
from test.util import build_grab
from test.util import BaseGrabTestCase
import six

from grab.stat import Stat


class GrabStatTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_zero_division_error(self):
        stat = Stat()
        stat.get_speed_line(stat.time)
