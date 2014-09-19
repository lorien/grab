import re

from grab.error import DataNotFound
from grab.tools.text import normalize_space
from grab.tools.html import decode_entities
from grab.util.py3k_support import *

REGEXP_CACHE = {}
NULL = object()


def extract_rex_list(rex, body):
    """
    Return found matches.
    """

    return rex.findall(body)


def cache_regexp(rex, flags=0):
    key = (rex, flags)
    try:
        return REGEXP_CACHE[key]
    except KeyError:
        obj = re.compile(rex, flags)
        #obj.source = rex
        REGEXP_CACHE[key] = obj
        return obj


def rex(body, regexp, flags=0, byte=False, default=NULL):
    """
    Search `regexp` expression in `body` text.
    """

    regexp = normalize_regexp(regexp, flags)
    match =  regexp.search(body)
    if match:
        return match
    else:
        if default is NULL:
            raise DataNotFound('Could not find regexp: %s' % regexp)
        else:
            return default


def rex_text(body, regexp, flags=0, default=NULL):
    """
    Search `regexp` expression in `body` text and then strip tags in found result.
    """

    match = rex(body, regexp, flags=flags, default=default)
    try:
        return normalize_space(decode_entities(match.group(1)))
    except AttributeError:
        if default is NULL:
            raise DataNotFound('Regexp not found')
        else:
            return default


def normalize_regexp(regexp, flags=0):
    """
    Accept string or compiled regular expression object.

    Compile string into regular expression object.
    """

    if isinstance(regexp, basestring):
        return cache_regexp(regexp, flags)
    else:
        return regexp


def rex_list(body, rex, flags=0):
    """
    Return found matches.
    """

    rex = normalize_regexp(rex, flags)
    return list(rex.finditer(body))


def rex_text_list(body, rex, flags=0):
    """
    Return found matches with stripped tags.
    """

    items = []
    for match in rex_list(body, rex, flags=flags):
        items.append(normalize_space(decode_entities(match.group(1))))
    return items
