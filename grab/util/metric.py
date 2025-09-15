KB = 1024
MB = 1024 * KB
GB = MB * 1024


def in_unit(num, unit):
    if unit == "b":
        return num
    elif unit == "kb":
        return round(num / float(KB), 2)
    elif unit == "mb":
        return round(num / float(MB), 2)
    elif unit == "gb":
        return round(num / float(GB), 2)
    else:
        return num


def format_traffic_value(num):
    if num < KB:
        return "%s B" % in_unit(num, "b")
    elif num < MB:
        return "%s KB" % in_unit(num, "kb")
    elif num < GB:
        return "%s MB" % in_unit(num, "mb")
    else:
        return "%s GB" % in_unit(num, "gb")
