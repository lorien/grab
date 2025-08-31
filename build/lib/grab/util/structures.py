from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import Any


def merge_with_dict(
    hdr1: MutableMapping[str, Any],
    hdr2: Mapping[str, Any],
    replace: bool,
) -> MutableMapping[str, Any]:
    for key, val in hdr2.items():
        if replace or key not in hdr1:
            hdr1[key] = val
    return hdr1
