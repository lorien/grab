def make_str(value, encoding="utf-8", errors="strict"):
    """Normalize unicode/byte string to unicode string."""
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode(encoding, errors=errors)
    return str(value)


def make_bytes(value, encoding="utf-8", errors="strict"):
    """Normalize unicode/byte string to byte string."""
    if isinstance(value, str):
        return value.encode(encoding, errors=errors)
    if isinstance(value, bytes):
        return value
    return str(value).encode(encoding, errors=errors)


def decode_pairs(pairs, encoding="utf-8"):
    def decode(value):
        if isinstance(value, bytes):
            return make_str(value, encoding)
        return value

    return [(decode(pair[0]), decode(pair[1])) for pair in pairs]
