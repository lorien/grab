from __future__ import annotations

import codecs
from collections.abc import Sequence
from typing import Any

# Reference:
# * https://github.com/scrapy/w3lib/blob/master/w3lib/encoding.py
# * https://docs.python.org/3/library/codecs.html
BOM_TABLE = [
    (codecs.BOM_UTF32_BE, "utf-32-be"),
    (codecs.BOM_UTF32_LE, "utf-32-le"),
    (codecs.BOM_UTF16_BE, "utf-16-be"),
    (codecs.BOM_UTF16_LE, "utf-16-le"),
    (codecs.BOM_UTF8, "utf-8"),
]
BOM_FIRST_CHARS = {char[0] for (char, _) in BOM_TABLE}


def make_str(value: Any, encoding: str = "utf-8", errors: str = "strict") -> str:
    """Normalize unicode/byte string to unicode string."""
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode(encoding, errors=errors)
    return str(value)


def make_bytes(value: Any, encoding: str = "utf-8", errors: str = "strict") -> bytes:
    """Normalize unicode/byte string to byte string."""
    if isinstance(value, str):
        return value.encode(encoding, errors=errors)
    if isinstance(value, bytes):
        return value
    return str(value).encode(encoding, errors=errors)


def decode_bytes(value: Any, encoding: str) -> Any:
    if isinstance(value, bytes):
        return value.decode(encoding)
    return value


def decode_pairs(
    pairs: Sequence[tuple[str | bytes, Any]], encoding: str = "utf-8"
) -> Sequence[tuple[str, str]]:
    ret = []
    for pair in pairs:
        ret.append((decode_bytes(pair[0], encoding), decode_bytes(pair[1], encoding)))
    return ret


def read_bom(data: bytes) -> tuple[None, None] | tuple[str, bytes]:
    """Detect BOM and encoding it is representing.

    Read the byte order mark in the text, if present, and
    return the encoding represented by the BOM and the BOM.

    If no BOM can be detected, (None, None) is returned.
    """
    # common case is no BOM, so this is fast
    if data and data[0] in BOM_FIRST_CHARS:
        for bom, encoding in BOM_TABLE:
            if data.startswith(bom):
                return encoding, bom
    return None, None
