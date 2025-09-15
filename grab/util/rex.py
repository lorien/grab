import re

import six

REGEXP_CACHE = {}


def cache_regexp(rex, flags=0):
    key = (rex, flags)
    try:
        return REGEXP_CACHE[key]
    except KeyError:
        obj = re.compile(rex, flags)
        # obj.source = rex
        REGEXP_CACHE[key] = obj
        return obj


def normalize_regexp(regexp, flags=0):
    """
    Accept string or compiled regular expression object.

    Compile string into regular expression object.
    """

    if isinstance(regexp, six.string_types):
        return cache_regexp(regexp, flags)
    else:
        return regexp
