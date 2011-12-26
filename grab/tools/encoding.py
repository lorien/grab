def smart_str(value, encoding='utf-8'):
    """
    Normalize unicode/btye string to byte string.
    """

    if isinstance(value, unicode):
        value = value.encode(encoding)
    return value
