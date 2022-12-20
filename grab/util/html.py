from __future__ import annotations

import html
import re

RE_REFRESH_TAG = re.compile(r'<meta[^>]+http-equiv\s*=\s*["\']*Refresh[^>]+', re.I)
# <meta http-equiv='REFRESH' content='0;url= http://www.bk55.ru/mc2/news/article/855'>
RE_REFRESH_URL = re.compile(
    r"content \s* = \s* ['\"]* \s* \d+ \s*"
    r";?  (?: \s* url \s* = \s*)?"
    r"['\"]* ([^'\"> ]*)",
    re.I | re.X,
)
RE_BASE_URL = re.compile(r"<base[^>]+href\s*=['\"]*([^'\"> ]+)", re.I)


def find_refresh_url(content: str) -> None | str:
    """Find value of redirect url from http-equiv refresh meta tag."""
    # We must decode num and named entities to correctly find refresh URL value
    tag_match = RE_REFRESH_TAG.search(html.unescape(content))
    if tag_match:
        url_match = RE_REFRESH_URL.search(tag_match.group(0))
        if url_match:
            return url_match.group(1)
    return None


def find_base_url(content: str) -> None | str:
    """Find url of <base> tag."""
    match = RE_BASE_URL.search(html.unescape(content))
    if match:
        return match.group(1)
    return None
