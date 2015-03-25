# coding: utf-8
from unittest import TestCase
import six
from codecs import open
from tools.encoding import make_str
from grab.export.mysql_dumper import MysqlCSVDumper, build_import_sql

from test.util import get_temp_file

IMPORT_SQL = r'''LOAD DATA LOCAL INFILE "/tmp/x.sql"
REPLACE INTO TABLE foo
character set utf8
fields terminated by "," optionally enclosed by '"'
lines terminated by "\r\n"
(col1,col2);'''

class MysqlCSVDumperTestCase(TestCase):
    def test_constructor(self):
        path = get_temp_file()
        MysqlCSVDumper(path)

    def test_normalize_none_value(self):
        path = get_temp_file()
        dumper = MysqlCSVDumper(path)
        dumper.add_row((None,))
        dumper.close()
        self.assertTrue(r'\N' in open(path, encoding='utf-8').read())

    def test_normalize_unicode(self):
        path = get_temp_file()
        dumper = MysqlCSVDumper(path)
        dumper.add_row((u'фуу',))
        dumper.close()
        self.assertTrue(u'фуу' in open(path, encoding='utf-8').read())

    def test_normalize_bytes(self):
        path = get_temp_file()
        dumper = MysqlCSVDumper(path)
        dumper.add_row((make_str('фуу'),))
        dumper.close()
        self.assertTrue(u'фуу' in open(path, encoding='utf-8').read())

    def test_normalize_int(self):
        path = get_temp_file()
        dumper = MysqlCSVDumper(path)
        dumper.add_row((1,))
        dumper.close()
        self.assertTrue(u'1' in open(path, encoding='utf-8').read())

    def test_build_import_sql(self):
        self.assertEqual(
            IMPORT_SQL, build_import_sql('/tmp/x.sql', 'foo', ['col1', 'col2']))
