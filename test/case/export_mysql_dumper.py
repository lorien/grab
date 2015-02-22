from unittest import TestCase

from test.util import get_temp_file
from grab.export.mysql_dumper import MysqlCSVDumper

class MysqlCSVDumperTestCase(TestCase):
    def test_constructor(self):
        path = get_temp_file()
        dumper = MysqlCSVDumper(path)
