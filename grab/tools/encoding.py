import re

RE_SPECIAL_ENTITY = re.compile('&#(1[2-6][0-9]);')

def smart_str(value, encoding='utf-8'):
    """
    Normalize unicode/byte string to byte string.
    """

    if isinstance(value, unicode):
        value = value.encode(encoding)
    return value


def smart_unicode(value, encoding='utf-8'):
    """
    Normalize unicode/btye string to unicode string.
    """

    if not isinstance(value, unicode):
        value = value.decode(encoding)
    return value


def special_entity_handler(match):
    num = int(match.group(1))
    if 128 <= num <= 160:
        try:
            return '&#%d;' % ord(chr(num).decode('cp1252'))
        except UnicodeDecodeError:
            return match.group(0)
    else:
        return match.group(0)


def fix_special_entities(body):
    return RE_SPECIAL_ENTITY.sub(special_entity_handler, body)
