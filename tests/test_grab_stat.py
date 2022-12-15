from grab.stat import Stat
from tests.util import BaseGrabTestCase


class GrabStatTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_zero_division_error(self):
        stat = Stat()
        stat.get_speed_line(stat.time)