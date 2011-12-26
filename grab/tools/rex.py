import re

from ..base import DataNotFound
from .text import normalize_space
from .html import decode_entities

CACHE = {}
NULL = object()

def extract_rex_list(rex, body):
    """
    Return found matches.
    """

    return rex.findall(body)


def rex_cache(rex, flags=0):
    key = (rex, flags)
    try:
        return CACHE[key]
    except KeyError:
        obj = re.compile(rex, flags)
        #obj.source = rex
        CACHE[key] = obj
        return obj


def rex_text(body, regexp, flags=0, default=NULL):
    match = rex(body, regexp, flags=flags, default=default)
    try:
        return normalize_space(decode_entities(match.group(1)))
    except AttributeError:
        raise DataNotFound('Regexp not found')
   

def rex(body, regexp, flags=0, byte=False, default=NULL):
    regexp = normalize_regexp(regexp, flags)
    match =  regexp.search(body)
    if match:
        return match
    else:
        if default is NULL:
            raise DataNotFound('Could not find regexp: %s' % regexp)
        else:
            return default


def normalize_regexp(regexp, flags=0):
    """
    Accept string or compiled regular expression object.

    Compile string into regular expression object.
    """

    if isinstance(regexp, basestring):
        return rex_cache(regexp, flags)
    else:
        return regexp


def rex_list(body, rex, flags=0):
    """
    Return found matches.
    """

    rex = normalize_regexp(rex, flags)
    return rex.finditer(body)

def rex_text_list(body, rex, flags=0):
    """
    Return found matches.
    """

    items = []
    for match in rex_list(body, rex, flags=flags):
        items.append(normalize_space(decode_entities(match.group(1))))
    return items
