def make_str(value, encoding="utf-8", errors="strict"):
    """
    Normalize unicode/byte string to unicode string.
    """

    if isinstance(value, str):
        return value
    elif isinstance(value, bytes):
        return value.decode(encoding, errors=errors)
    else:
        return str(value)


def make_bytes(value, encoding="utf-8", errors="strict"):
    """
    Normalize unicode/byte string to byte string.
    """

    if isinstance(value, str):
        return value.encode(encoding, errors=errors)
    elif isinstance(value, bytes):
        return value
    else:
        return str(value).encode(encoding, errors=errors)


def decode_pairs(pairs, encoding="utf-8"):
    def decode(value):
        if isinstance(value, bytes):
            return make_str(value, encoding)
        else:
            return value

    return [(decode(pair[0]), decode(pair[1])) for pair in pairs]
