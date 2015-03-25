import csv
import six
from tools.encoding import make_str, make_unicode


class CSVDumper(object):
    def __init__(self, path, fields=None, write_header=True,
                 quoting=csv.QUOTE_ALL):
        self.path = path
        self.fields = fields
        self.write_header = write_header
        self.file_handler = open(path, 'w')
        self.writer = csv.writer(self.file_handler, quoting=quoting)
        if self.fields and self.write_header:
            self.writer.writerow(
                self.normalize_unicode_row(self.normalize_row(self.fields)))

    def add_record(self, rec, ignore_fields=None):
        if ignore_fields is None:
            ignore_fields = []
        if self.fields is None:
            raise Exception('Can not use `add_record` if `fields` is not set')
        for key in rec:
            if key not in ignore_fields:
                if key not in self.fields:
                    raise Exception('Unknown record key: %s' % key)
        for key in self.fields:
            if key not in rec:
                raise Exception('Missing key in record: %s' % key)
        row = [rec[x] for x in self.fields]
        self.writer.writerow(self.normalize_row(row))

    def add_row(self, row):
        self.writer.writerow(
            self.normalize_unicode_row(self.normalize_row(row)))

    def normalize_unicode_row(self, row):
        return list(map(make_unicode if six.PY3 else make_str, row))

    def normalize_row(self, row):
        return list(map(self.normalize_value, row))

    def normalize_none_value(self, val):
        return ''

    def normalize_value(self, val):
        if val is None:
            return self.normalize_none_value(val)
        elif isinstance(val, six.text_type):
            if six.PY3:
                return val
            else:
                return val.encode('utf-8')
        else:
            return str(val)

    def close(self):
        self.file_handler.close()
