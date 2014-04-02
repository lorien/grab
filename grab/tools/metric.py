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


def in_unit(num, unit):
    if unit == 'b':
        return num
    elif unit == 'kb':
        return round(num / float(KB), 2)
    elif unit == 'mb':
        return round(num / float(MB), 2)
    elif unit == 'gb':
        return round(num / float(GB), 2)
    else:
        return num


def parse_size(size, unit='b'):
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
                return in_unit(val, unit)
        return 0


def format_traffic_value(num):
    if num < KB:
        return '%s B' % in_unit(num, 'b')
    elif num < MB:
        return '%s KB' % in_unit(num, 'kb')
    elif num < GB:
        return '%s MB' % in_unit(num, 'mb')
    else:
        return '%s GB' % in_unit(num, 'gb')
