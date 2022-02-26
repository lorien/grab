from pprint import pprint  # pylint: disable=unused-import

from test_server import Response  # pylint: disable=unused-import

from grab.util.log import default_logging

from tests.util import build_grab  # pylint: disable=unused-import
from tests.util import BaseGrabTestCase, temp_file


class TestMisc(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_default_logging(self):
        with temp_file() as grab_network_file:
            with temp_file() as grab_file:
                default_logging(network_log=grab_network_file, grab_log=grab_file)
