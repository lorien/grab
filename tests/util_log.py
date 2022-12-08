from unittest import TestCase

from grab.util.log import default_logging
from tests.util import temp_file


class UtilLogTestCase(TestCase):
    def test_default_logging(self):
        with temp_file() as grab_network_file, temp_file() as grab_file:
            default_logging(network_log=grab_network_file, grab_log=grab_file)
