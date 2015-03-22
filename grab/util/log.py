"""
This module contains `print_dict` function that is useful
to dump content of dictionary in human acceptable representation.
"""
import six


def repr_value(val):
    if isinstance(val, six.text_type):
        return val.encode('utf-8')
    elif isinstance(val, (list, tuple)):
        return b'[' + b', '.join(repr_value(x) for x in val) + b']'
    elif isinstance(val, dict):
        return b'{' + b', '.join((repr_value(x) + b': ' + repr_value(y))
                               for x, y in val.items()) + b'}'
    else:
        return six.b(str(val))


def print_dict(dic):
    print(b'[---')
    for key, val in sorted(dic.items(), key=lambda x: x[0]):
        print(repr_value(key) + b': ' + repr_value(val))
    print(b'---]')
