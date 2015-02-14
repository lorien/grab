import csv


class CSVDumper(object):
    def __init__(self, path, fields=None, write_header=True,
                 quoting=csv.QUOTE_ALL):
        self.path = path
        self.fields = fields
        self.write_header = write_header
        self.file_handler = open(path, 'w')
        self.writer = csv.writer(self.file_handler, quoting=quoting)
        if self.fields and self.write_header:
            self.writer.writerow(self.normalize_row(self.fields))

    def add_record(self, rec, ignore_fields=None):
        if ignore_fields is None:
            ignore_fields = []
        if self.fields is None:
            raise Exception('Can not use `add_record` if `fields` is not set')
        for key in rec:
            if not key in ignore_fields:
                if not key in self.fields:
                    raise Exception('Unknown record key: %s' % key)
        for key in self.fields:
            if not key in rec:
                raise Exception('Missing key in record: %s' % key)
        row = [rec[x] for x in self.fields]
        self.writer.writerow(self.normalize_row(row))

    def add_row(self, row):
        self.writer.writerow(self.normalize_row(row))

    def normalize_row(self, row):
        return map(self.normalize_value, row)

    def normalize_none_value(self, val):
        return ''

    def normalize_value(self, val):
        if val is None:
            return self.normalize_none_value(val)
        elif isinstance(val, unicode):
            return val.encode('utf-8')
        else:
            return str(val)

    def close(self):
        self.file_handler.close()
