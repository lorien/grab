def repr_value(val):
    if isinstance(val, unicode):
        return val.encode('utf-8')
    elif isinstance(val, (list, tuple)):
        return '[%s]' % ', '.join(repr_val(x) for x in val)
    elif isinstance(val, dict):
        return '{%s}' % ', '.join('%s: %s' % (repr_val(x), repr_val(y)) for x, y in val.items())
    else:
        return str(val)


def print_dict(dic):
    print '[---'
    for key, val in sorted(dic.items(), key=lambda x: x[0]):
        print key, ':', repr_value(val)
    print '---]'
