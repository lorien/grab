import re

from grab.util.py3k_support import *

RE_SPECIAL_ENTITY = re.compile(b'&#(1[2-6][0-9]);')


def make_str(value, encoding='utf-8', errors='strict'):
    """
    Normalize unicode/byte string to byte string.
    """

    if isinstance(value, unicode):
        # Convert to string (py2.x) or bytes (py3.x)
        value = value.encode(encoding, errors=errors)
    elif isinstance(value, str):
        pass
    else:
        value = str(value)
    return value


def make_unicode(value, encoding='utf-8', errors='strict'):
    """
    Normalize unicode/byte string to unicode string.
    """

    if not isinstance(value, unicode):
        # Convert to unicode (py2.x and py3.x)
        value = value.decode(encoding, errors=errors)
    return value


def special_entity_handler(match):
    num = int(match.group(1))
    if 128 <= num <= 160:
        try:
            num = unichr(num).encode('utf-8')
            return smart_str('&#%d;' % ord(num.decode('cp1252')[1]))
        except UnicodeDecodeError:
            return match.group(0)
    else:
        return match.group(0)


def fix_special_entities(body):
    return RE_SPECIAL_ENTITY.sub(special_entity_handler, body)


def decode_list(values, encoding='utf-8'):
    if not isinstance(values, list):
        raise TypeError('unsupported values type: %s' % type(values))
    return [smart_unicode(value, encoding) for value in values]


def decode_dict(values, encoding='utf-8'):
    if not isinstance(values, dict):
        raise TypeError('unsupported values type: %s' % type(values))
    return dict(decode_pairs(values.items(), encoding))


def decode_pairs(pairs, encoding='utf-8'):
    def decode(value):
        return smart_unicode(value, encoding)

    return [(decode(pair[0]), decode(pair[1])) for pair in pairs]

# Backward compatibility
smart_str = make_str
smart_unicode = make_unicode
