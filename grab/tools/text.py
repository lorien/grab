"""
Text parsing and processing utilities.
"""
import re

RE_NUMBER = re.compile(r'\d+')
RE_NUMBER_WITH_SPACES = re.compile(r'\d[\s\d]*', re.U)
RE_SPACE = re.compile(r'\s+', re.U)

def find_number(text, ignore_spaces=False):
    """
    Find the number in the `text`.

    :param text: unicode or byte-string text
    :param ignore_spacess: if True then groups of digits delimited
        by spaces are considered as one number
    :raises: :class:`DataNotFound` if number was not found.
    """
    # tmp hack
    # to avoid import error
    from ..base import DataNotFound

    if ignore_spaces:
        match = RE_NUMBER_WITH_SPACES.search(text)
    else:
        match = RE_NUMBER.search(text)
    if match:
        if ignore_spaces:
            return drop_space(match.group(0))
        else:
            return match.group(0)
    else:
        raise DataNotFound

def drop_space(text):
    """
    Drop all space-chars in the `text`.
    """

    return RE_SPACE.sub('', text)

def normalize_space(text):
    """
    Replace sequence of space-chars with one space char.

    Also drop leading and trailing space-chars.
    """

    return RE_SPACE.sub(' ', text).strip()
