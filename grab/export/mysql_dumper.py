import csv

from grab.export.csv_dumper import CSVDumper


class MysqlCSVDumper(CSVDumper):
    """
    Difference from CSVDumper:
    * default `quoting` value is QUOTE_MINIMAL
    * default `write_header` value is False
    * None values are converted to r'\N'
    * \ symbols are converted to \\
    """

    def __init__(self, path, fields=None, write_header=False,
                 quoting=csv.QUOTE_MINIMAL):
        super(MysqlCSVDumper, self).__init__(path, fields=fields,
                                             write_header=write_header,
                                             quoting=quoting)

    def normalize_none_value(self, val):
        return r'\N'

    def normalize_value(self, val):
        if val is None:
            return self.normalize_none_value(val)
        elif isinstance(val, basestring):
            if isinstance(val, basestring):
                val = val.encode('utf-8')
            val = val.replace('\\', '\\\\')
            return val
        else:
            return str(val)


def build_import_sql(path, table, columns):
    sql = r'''
        LOAD DATA LOCAL INFILE "%s"
        REPLACE INTO TABLE %s
        character set utf8
        fields terminated by "," optionally enclosed by '"'
        lines terminated by "\r\n"
        (%s);
    ''' % (path, table, ','.join(columns))
    sql = '\n'.join(x.lstrip() for x in sql.splitlines() if x.strip())
    return sql
