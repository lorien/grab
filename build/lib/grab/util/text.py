import re


def normalize_spaces(val: str) -> str:
    return re.sub(r"\s+", " ", val).strip()
