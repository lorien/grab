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
