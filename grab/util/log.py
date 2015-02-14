"""
This module contains `print_dict` function that is useful
to dump content of dictionary in human acceptable representation.
"""


def repr_value(val):
    if isinstance(val, unicode):
        return val.encode('utf-8')
    elif isinstance(val, (list, tuple)):
        return '[%s]' % ', '.join(repr_value(x) for x in val)
    elif isinstance(val, dict):
        return '{%s}' % ', '.join('%s: %s' % (repr_value(x), repr_value(y))
                                  for x, y in val.items())
    else:
        return str(val)


def print_dict(dic):
    print('[---')
    for key, val in sorted(dic.items(), key=lambda x: x[0]):
        print(key, ':', repr_value(val))
    print ('---]')
