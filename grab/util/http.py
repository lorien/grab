import re
from urllib.parse import quote, urlencode, urlsplit, urlunsplit

from .encoding import make_bytes, make_str

GEN_DELIMS = r":/?#[]@"
SUB_DELIMS = r"!$&\'()*+,;="
RESERVED_CHARS = GEN_DELIMS + SUB_DELIMS + "%"
UNRESERVED_CHARS = r"-._~a-zA-Z0-9"
RE_NOT_SAFE_CHAR = re.compile(
    r"[^" + UNRESERVED_CHARS + re.escape(RESERVED_CHARS) + "]"
)
RE_NON_ALPHA_DIGIT_NETLOC = re.compile(r"[^-.:@a-zA-Z0-9]")


def smart_urlencode(items, charset="utf-8"):
    """
    Normalize items to be a part of HTTP request's payload.

    It differs from ``urllib.urlencode`` in that it can process unicode
    and some special values.

    ``items`` could dict or tuple or list.
    """
    if isinstance(items, dict):
        items = items.items()
    res = normalize_http_values(items, charset=charset)
    return urlencode(res)


def process_http_item(item, charset, ignore_classes):
    key, value = item
    if isinstance(value, (list, tuple)):
        ret = []
        for subval in value:
            ret.extend(process_http_item((key, subval), charset, ignore_classes))
        return ret
    if isinstance(key, str):
        key = make_bytes(key, encoding=charset)
    if ignore_classes and isinstance(value, ignore_classes):
        pass
    elif isinstance(value, str):
        value = make_bytes(value, encoding=charset)
    elif value is None:
        value = b""
    else:
        value = make_bytes(value)
    return [(key, value)]


def normalize_http_values(items, charset="utf-8", ignore_classes=None):
    """
    Convert values in dict/list-of-tuples to bytes.

    Unicode is converted into bytestring using charset of previous response
    (or utf-8, if no requests were performed)

    None is converted into empty string.

    If `ignore_classes` is not None and the value is instance of
    any classes from the `ignore_classes` then the value is not
    processed and returned as-is.
    """
    if isinstance(items, dict):
        items = items.items()

    # Fix list into tuple because isinstance works only with tupled sequences
    if isinstance(ignore_classes, list):
        ignore_classes = tuple(ignore_classes)

    ret = []
    for item in items:
        ret.extend(process_http_item(item, charset, ignore_classes))
    return ret


def normalize_url(url):
    # https://tools.ietf.org/html/rfc3986
    url = make_str(url)
    if RE_NOT_SAFE_CHAR.search(url):
        parts = list(urlsplit(url))
        # Scheme
        # do nothing with scheme
        # Network location (user:pass@hostname)
        if RE_NON_ALPHA_DIGIT_NETLOC.search(parts[1]):
            parts[1] = parts[1].encode("idna")
        # Path
        parts[2] = quote(make_str(parts[2]), safe=RESERVED_CHARS)
        # Query
        parts[3] = quote(make_str(parts[3]), safe=RESERVED_CHARS)
        # Fragment
        parts[4] = quote(make_str(parts[4]), safe=RESERVED_CHARS)
        return urlunsplit(map(make_str, parts))
    return url


def normalize_post_data(data, encoding="utf-8"):
    if isinstance(data, str):
        return make_bytes(data, encoding=encoding)
    if isinstance(data, bytes):
        return data
    # it calls `normalize_http_values()`
    res = smart_urlencode(data, encoding)
    return make_bytes(res)
