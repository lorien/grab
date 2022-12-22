from __future__ import annotations

import html
import re

RE_BASE_URL = re.compile(r"<base[^>]+href\s*=['\"]*([^'\"> ]+)", re.I)


def find_base_url(content: str) -> None | str:
    """Find value of attribute "url" in "<base>" tag."""
    match = RE_BASE_URL.search(html.unescape(content))
    if match:
        return match.group(1)
    return None
