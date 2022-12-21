from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote, urlencode, urlsplit, urlunsplit

from ..upload import BaseUploadItem
from .encoding import make_bytes

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


# def smart_urlencode(
#    items: dict[str, Any]| list[tuple[str, Any]], charset: str = "utf-8"
# ) -> str:
#    """
#    Normalize items to be a part of HTTP request's payload.
#
#    WOW, so much smart.
#
#    It differs from ``urllib.urlencode`` in that it can process unicode
#    and some special values.
#    """
#    if isinstance(items, dict):
#        items = list(items.items())
#    res = normalize_http_values(items, charset=charset)
#    return urlencode(res)


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
        key = make_bytes(key, encoding=charset)
    # value
    if isinstance(value, BaseUploadItem):
        pass
    elif isinstance(value, str):
        value = make_bytes(value, encoding=charset)
    elif value is None:
        value = b""
    else:
        value = make_bytes(value)
    return [(key, value)]


def normalize_http_values(
    items: dict[str, Any] | list[tuple[str, Any]],
    charset: str = "utf-8",
) -> list[tuple[bytes, Any]]:
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


def normalize_post_data(data: str | bytes, encoding: str = "utf-8") -> bytes:
    if isinstance(data, str):
        return data.encode(encoding)
    if isinstance(data, bytes):
        return data
    # it calls `normalize_http_values()`
    return make_bytes(urlencode(normalize_http_values(data, encoding)))
