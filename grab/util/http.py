from __future__ import annotations

import re
import typing
from typing import Any, cast
from urllib.parse import quote, urlencode, urlsplit, urlunsplit

from ..upload import BaseUploadItem

GEN_DELIMS = r":/?#[]@"
SUB_DELIMS = r"!$&\'()*+,;="
RESERVED_CHARS = GEN_DELIMS + SUB_DELIMS + "%"
UNRESERVED_CHARS = r"-._~a-zA-Z0-9"
RE_NOT_SAFE_CHAR = re.compile(
    r"[^" + UNRESERVED_CHARS + re.escape(RESERVED_CHARS) + "]"
)
RE_NON_ALPHA_DIGIT_NETLOC = re.compile(r"[^-.:@a-zA-Z0-9]")


def normalize_url(input_url: bytes | str) -> str:
    # https://tools.ietf.org/html/rfc3986
    url: str = input_url if isinstance(input_url, str) else input_url.decode("utf-8")
    if RE_NOT_SAFE_CHAR.search(url):
        parts = list(urlsplit(url))
        # Scheme
        # do nothing with scheme
        # Network location (user:pass@hostname)
        if RE_NON_ALPHA_DIGIT_NETLOC.search(parts[1]):
            parts[1] = parts[1].encode("idna").decode("ascii")
        # Path
        parts[2] = quote(parts[2], safe=RESERVED_CHARS)
        # Query
        parts[3] = quote(parts[3], safe=RESERVED_CHARS)
        # Fragment
        parts[4] = quote(parts[4], safe=RESERVED_CHARS)
        return urlunsplit(parts)
    return url


def process_http_item(
    item: tuple[str | bytes, Any],
    charset: str,
) -> list[tuple[bytes, bytes | BaseUploadItem]]:
    key: str | bytes = item[0]
    value: Any = item[1]
    if isinstance(value, (list, tuple)):
        ret = []
        for subval in value:
            ret.extend(process_http_item((key, subval), charset))
        return ret
    # key
    if isinstance(key, str):
        key = key.encode(encoding=charset)
    # value
    if isinstance(value, BaseUploadItem):
        pass
    elif isinstance(value, str):
        value = value.encode(encoding=charset)
    elif value is None:
        value = b""
    else:
        value = str(value).encode(encoding=charset)
    return [(key, value)]


def normalize_http_values(
    items: dict[str, Any] | list[tuple[str, Any]],
    charset: str = "utf-8",
) -> list[tuple[bytes, bytes | BaseUploadItem]]:
    """Convert values in dict/list-of-tuples to bytes.

    Unicode is converted into bytestring using charset of previous response
    (or utf-8, if no requests were performed)

    None is converted into empty string.

    If value is instance of BaseUploadItem subclass then the value is not
    processed.
    """
    if isinstance(items, dict):
        items = list(items.items())
    # Fix list into tuple because isinstance works only with tupled sequences
    ret = []
    for item in items:
        ret.extend(process_http_item(item, charset))
    return ret


def normalize_post_data(
    data: str | bytes | dict[str, Any] | list[tuple[str, Any]], encoding: str = "utf-8"
) -> bytes:
    if isinstance(data, str):
        return data.encode(encoding)
    if isinstance(data, bytes):
        return data
    # pylint: disable=deprecated-typing-alias
    return urlencode(
        cast(
            typing.List[typing.Tuple[bytes, bytes]],
            normalize_http_values(data, encoding),
        )
    ).encode("utf-8")
