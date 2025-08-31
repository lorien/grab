from __future__ import annotations

from collections.abc import Sequence
from typing import Any


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
