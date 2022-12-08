import re


def normalize_regexp(regexp, flags=0):
    """
    Accept string or compiled regular expression object.

    Compile string into regular expression object.
    """

    if isinstance(regexp, str):
        return re.compile(regexp, flags)
    return regexp
