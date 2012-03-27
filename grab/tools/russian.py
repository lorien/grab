# coding: utf-8
from __future__ import absolute_import

from ..tools.encoding import smart_unicode
from pytils.translit import translify
import re

RE_NOT_ENCHAR = re.compile(ur'[^-a-zA-Z0-9]', re.U)
RE_NOT_ENRUCHAR = re.compile(ur'[^-a-zA-Zа-яА-ЯёЁ0-9]', re.U)
RE_RUSSIAN_CHAR = re.compile(ur'[а-яА-ЯёЁ]', re.U)
RE_DASH = re.compile(r'-+')

def slugify(value, limit=None, default=''):
    value = smart_unicode(value)

    # Replace all non russian/english chars with "-" char
    # to help pytils not to crash
    value = RE_NOT_ENRUCHAR.sub('-', value)

    # Do transliteration
    value = translify(value)

    # Replace trash with safe "-" char
    value = RE_NOT_ENCHAR.sub('-', value).strip('-').lower()

    # Replace sequences of dashes
    value = RE_DASH.sub('-', value)

    if limit is not None:
        value = value[:limit]

    if value != "":
        return value
    else:
        return default
