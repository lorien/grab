from __future__ import annotations

import codecs
import re
from typing import cast

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


RE_META_CHARSET = re.compile(rb"<meta[^>]+content\s*=\s*[^>]+charset=([-\w]+)", re.I)
RE_META_CHARSET_HTML5 = re.compile(rb'<meta[^>]+charset\s*=\s*[\'"]?([-\w]+)', re.I)
RE_DECLARATION_ENCODING = re.compile(rb'encoding\s*=\s*["\']([^"\']+)["\']')
RE_XML_DECLARATION = re.compile(rb"^[^<]{,100}<\?xml[^>]+\?>", re.I)


def parse_bom(data: bytes) -> tuple[None, None] | tuple[str, bytes]:
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


def parse_document_charset(
    data_chunk: bytes,
) -> tuple[None | str, None | bytes]:
    charset: None | str = None
    ret_bom: None | bytes = None
    # Try to extract charset from http-equiv meta tag
    match_charset = RE_META_CHARSET.search(data_chunk)
    if match_charset:
        charset = match_charset.group(1).decode("utf-8", "ignore")
    else:
        match_charset_html5 = RE_META_CHARSET_HTML5.search(data_chunk)
        if match_charset_html5:
            charset = match_charset_html5.group(1).decode("utf-8", "ignore")

    # TODO: <meta charset="utf-8" />
    bom_encoding, chunk_bom = parse_bom(data_chunk)
    if bom_encoding:
        charset = bom_encoding
        ret_bom = chunk_bom

    # Try to process XML declaration
    if not charset and data_chunk.startswith(b"<?xml"):
        match = RE_XML_DECLARATION.search(data_chunk)
        if match:
            enc_match = RE_DECLARATION_ENCODING.search(match.group(0))
            if enc_match:
                charset = cast(bytes, enc_match.group(1)).decode("utf-8", "ignore")
    return charset, ret_bom
