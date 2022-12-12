import re
from html.entities import name2codepoint
from typing import Match, Optional

from .encoding import make_bytes

RE_SPECIAL_ENTITY = re.compile(rb"&#(1[2-6][0-9]);")
RE_NAMED_ENTITY = re.compile(r"(&[a-z]+;)")
RE_NUM_ENTITY = re.compile(r"(&#[0-9]+;)")
RE_HEX_ENTITY = re.compile(r"(&#x[a-f0-9]+;)", re.I)
RE_REFRESH_TAG = re.compile(r'<meta[^>]+http-equiv\s*=\s*["\']*Refresh[^>]+', re.I)
# <meta http-equiv='REFRESH' content='0;url= http://www.bk55.ru/mc2/news/article/855'>
RE_REFRESH_URL = re.compile(
    r"""
    content \s* = \s*
    ["\']* \s* \d+ \s*
    ;?
    (?: \s* url \s* = \s*)?
    ["\']* ([^\'"> ]*)
""",
    re.I | re.X,
)
RE_BASE_URL = re.compile(r'<base[^>]+href\s*=["\']*([^\'"> ]+)', re.I)


def special_entity_handler(match: Match[bytes]) -> bytes:
    num = int(match.group(1))
    if 128 <= num <= 160:
        try:
            num_chr = chr(num).encode("utf-8")
            return make_bytes("&#%d;" % ord(num_chr.decode("cp1252")[1]))
        except UnicodeDecodeError:
            return match.group(0)
    else:
        return match.group(0)


def fix_special_entities(body: bytes) -> bytes:
    return RE_SPECIAL_ENTITY.sub(special_entity_handler, body)


def process_named_entity(match: Match[str]) -> str:
    entity = match.group(1)
    name = entity[1:-1]
    if name in name2codepoint:
        return chr(name2codepoint[name])
    return entity


def process_num_entity(match: Match[str]) -> str:
    entity = match.group(1)
    num = entity[2:-1]
    try:
        return chr(int(num))
    except ValueError:
        return entity


def process_hex_entity(match: Match[str]) -> str:
    entity = match.group(1)
    code = entity[3:-1]
    try:
        return chr(int(code, 16))
    except ValueError:
        return entity


def decode_entities(html: str) -> str:
    """Convert all HTML entities into their unicode representations.

    This functions processes following entities:
     * &XXX;
     * &#XXX;

    Example::

        >>> print html.decode_entities('&rarr;ABC&nbsp;&#82;&copy;')
        →ABC R©
    """
    html = RE_NUM_ENTITY.sub(process_num_entity, html)
    html = RE_HEX_ENTITY.sub(process_hex_entity, html)
    return RE_NAMED_ENTITY.sub(process_named_entity, html)


def find_refresh_url(html: str) -> Optional[str]:
    """Find value of redirect url from http-equiv refresh meta tag."""
    # We should decode quote values to correctly find
    # the url value
    # html = html.replace('&#39;', '\'')
    # html = html.replace('&#34;', '"').replace('&quot;', '"')
    html = decode_entities(html)

    match = RE_REFRESH_TAG.search(html)
    if match:
        match = RE_REFRESH_URL.search(match.group(0))
        if match:
            return match.group(1)
    return None


def find_base_url(html: str) -> Optional[str]:
    """Find url of <base> tag."""
    html = decode_entities(html)

    match = RE_BASE_URL.search(html)
    if match:
        return match.group(1)
    return None
