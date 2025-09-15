import re

from grab.error import DataNotFound

RE_NUMBER = re.compile(r"\d+")
RE_NUMBER_WITH_SPACES = re.compile(r"\d[\s\d]*", re.U)
RE_SPACE = re.compile(r"\s+", re.U)


def find_number(text, ignore_spaces=False, make_int=True, ignore_chars=None):
    """
    Find the number in the `text`.

    :param text: unicode or byte-string text
    :param ignore_spaces: if True then groups of digits delimited
        by spaces are considered as one number
    :raises: :class:`DataNotFound` if number was not found.
    """

    if ignore_chars:
        for char in ignore_chars:
            text = text.replace(char, "")
    if ignore_spaces:
        match = RE_NUMBER_WITH_SPACES.search(text)
    else:
        match = RE_NUMBER.search(text)
    if match:
        val = match.group(0)
        if ignore_spaces:
            val = drop_space(val)
        if make_int:
            val = int(val)
        return val
    else:
        raise DataNotFound


def drop_space(text):
    """
    Drop all space-chars in the `text`.
    """

    return RE_SPACE.sub("", text)


def normalize_space(text, replace=" "):
    """
    Replace sequence of space-chars with one space char.

    Also drop leading and trailing space-chars.
    """

    return RE_SPACE.sub(replace, text.strip()).strip()
