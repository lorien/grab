from __future__ import annotations

import re
from typing import Pattern, Union


def normalize_regexp(
    regexp: Union[str, bytes, Pattern[str], Pattern[bytes]], flags: int = 0
) -> Union[Pattern[bytes], Pattern[str]]:
    """Normalize string or regexp object to regexp object."""
    if isinstance(regexp, (bytes, str)):
        return re.compile(regexp, flags)
    return regexp
