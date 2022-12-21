from __future__ import annotations

from typing import Any


def make_bytes(value: Any, encoding: str = "utf-8", errors: str = "strict") -> bytes:
    """Normalize unicode/byte string to byte string."""
    if isinstance(value, str):
        return value.encode(encoding, errors=errors)
    if isinstance(value, bytes):
        return value
    return str(value).encode(encoding, errors=errors)
