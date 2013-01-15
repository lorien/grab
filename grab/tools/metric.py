# coding: utf-8
KB = 1024
MB = 1024 * KB
GB = MB * 1024


metric_labels = {
    u'mb': MB,
    u'мб': MB,
    u'kb': KB,
    u'кб': KB,
    u'gb': GB,
    u'гб': GB,
} 


def parse_size(size):
    size = size.lower().strip()
    if size.isdigit():
        return int(size)
    else:
        for anchor, mult in metric_labels.items():
            if anchor in size:
                size = size.replace(anchor, '')
                size = size.replace(',', '.')
                size = size.strip()
                val = int(float(size) * mult)
                return val
        return 0
