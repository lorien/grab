from __future__ import annotations

import re
from re import Pattern


def normalize_regexp(
    regexp: str | bytes | Pattern[str] | Pattern[bytes], flags: int = 0
) -> Pattern[bytes] | Pattern[str]:
    """Normalize string or regexp object to regexp object."""
    if isinstance(regexp, (bytes, str)):
        return re.compile(regexp, flags)
    return regexp
