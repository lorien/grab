import re


def normalize_regexp(regexp, flags=0):
    """Normalize string or regexp object to regexp object."""
    if isinstance(regexp, str):
        return re.compile(regexp, flags)
    return regexp
