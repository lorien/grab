from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import Any


def merge_with_dict(  # noqa: CCR001
    hdr1: MutableMapping[str, Any],
    hdr2: Mapping[str, Any],
    replace: bool,
) -> MutableMapping[str, Any]:
    # if isinstance(hdr1, Mapping):
    for key, val in hdr2.items():
        if replace or key not in hdr1:
            hdr1[key] = val
    return hdr1
    # else:
    #    ret = []
    #    hdr1_keys: set[str] = set()
    #    hdr2_keys: set[str] = set(hdr2)
    #    for key, val in hdr1:
    #        if not replace or key not in hdr2_keys:
    #            ret.append((key, val))
    #            hdr1_keys.add(key)
    #    for key, val in hdr2.items():
    #        if replace or key not in hdr1_keys:
    #            ret.append((key, val))
    #    return ret
