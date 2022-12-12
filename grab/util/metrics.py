from __future__ import annotations

KB = 1000
MB = 1000 * KB
GB = MB * 1000


def in_unit(num: int, unit: str) -> int | float:
    if unit == "b":
        return num
    if unit == "kb":
        return round(num / float(KB), 2)
    if unit == "mb":
        return round(num / float(MB), 2)
    if unit == "gb":
        return round(num / float(GB), 2)
    return num


def format_traffic_value(num: int) -> str:
    if num < KB:
        return "%s B" % in_unit(num, "b")
    if num < MB:
        return "%s KB" % in_unit(num, "kb")
    if num < GB:
        return "%s MB" % in_unit(num, "mb")
    return "%s GB" % in_unit(num, "gb")
