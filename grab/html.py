# -*- coding: utf-8 -*-
# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
import re
from htmlentitydefs import name2codepoint
import logging

RE_REFRESH_TAG = re.compile(r'<meta[^>]+http-equiv\s*=\s*["\']*Refresh[^>]+', re.I)
RE_REFRESH_URL = re.compile(r'url=["\']*([^\'"> ]+)', re.I)
RE_ENTITY = re.compile(r'(&[a-z]+;)')
RE_NUM_ENTITY = re.compile(r'(&#\d+;)')

def decode_entities(text):
    """
    Convert HTML entities to their unicode analogs.
    """


    def process_entity(match):
        entity = match.group(1)
        name = entity[1:-1]
        if name in name2codepoint:
            return unichr(name2codepoint[name])
        else:
            return entity

    
    def process_num_entity(match):
        entity = match.group(1)
        num = entity[2:-1]
        try:
            return unichr(int(num))
        except ValueError:
            return entity

    text = RE_NUM_ENTITY.sub(process_num_entity, text)
    text = RE_ENTITY.sub(process_entity, text)
    return text


def find_refresh_url(html):
    """
    Find value of redirect url from http-equiv refresh meta tag.
    """

    # We should decode quote values to correctly find
    # the url value
    #html = html.replace('&#39;', '\'')
    #html = html.replace('&#34;', '"').replace('&quot;', '"')
    html = decode_entities(html)

    match = RE_REFRESH_TAG.search(html)
    if match:
        match = RE_REFRESH_URL.search(match.group(0))
        if match:
            return match.group(1)
    return None
