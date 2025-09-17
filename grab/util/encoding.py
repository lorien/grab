import re

import six


def make_str(value, encoding="utf-8", errors="strict"):
    """
    Normalize unicode/byte string to byte string.
    """

    if isinstance(value, six.text_type):
        return value.encode(encoding, errors=errors)
    elif isinstance(value, six.binary_type):
        return value
    else:
        return six.u(str(value)).encode(encoding, errors=errors)


def make_unicode(value, encoding="utf-8", errors="strict"):
    """
    Normalize unicode/byte string to unicode string.
    """

    if isinstance(value, six.text_type):
        return value
    elif isinstance(value, six.binary_type):
        return value.decode(encoding, errors=errors)
    else:
        return six.u(str(value))


def decode_dict(values, encoding="utf-8"):
    if not isinstance(values, dict):
        raise TypeError("unsupported values type: %s" % type(values))
    return dict(decode_pairs(values.items(), encoding))


def decode_pairs(pairs, encoding="utf-8"):
    def decode(value):
        if isinstance(value, six.binary_type):
            return value.decode(encoding)
        else:
            return value

    return [(decode(pair[0]), decode(pair[1])) for pair in pairs]
