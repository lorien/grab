import re

import six

RE_SPECIAL_ENTITY = re.compile(b"&#(1[2-6][0-9]);")


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


def special_entity_handler(match):
    num = int(match.group(1))
    if 128 <= num <= 160:
        try:
            num = six.unichr(num).encode("utf-8")
            return make_str("&#%d;" % ord(num.decode("cp1252")[1]))
        except UnicodeDecodeError:
            return match.group(0)
    else:
        return match.group(0)


def fix_special_entities(body):
    return RE_SPECIAL_ENTITY.sub(special_entity_handler, body)


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
