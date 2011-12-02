import re

CACHE = {}

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
        CACHE[key] = obj
        return obj
