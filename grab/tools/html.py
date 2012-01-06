# -*- coding: utf-8 -*-
# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
import re
from htmlentitydefs import name2codepoint
import logging

from text import normalize_space as normalize_space_func

RE_TAG = re.compile(r'<[^>]+>')
RE_REFRESH_TAG = re.compile(r'<meta[^>]+http-equiv\s*=\s*["\']*Refresh[^>]+', re.I)
RE_REFRESH_URL = re.compile(r'url=["\']*([^\'"> ]+)', re.I)
RE_ENTITY = re.compile(r'(&[a-z]+;)')
RE_NUM_ENTITY = re.compile(r'(&#\d+;)')
RE_BASE_URL = re.compile(r'<base[^>]+href\s*=["\']*([^\'"> ]+)', re.I)

def decode_entities(html):
    """
    Convert all HTML entities into their unicode
    representations.

    This functions processes following entities:
     * &XXX;
     * &#XXX;

    Example::

        >>> print html.decode_entities('&rarr;ABC&nbsp;&#82;&copy;')
        →ABC R©
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

    html = RE_NUM_ENTITY.sub(process_num_entity, html)
    html = RE_ENTITY.sub(process_entity, html)
    return html


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


def find_base_url(html):
    """
    Find url of <base> tag.
    """

    html = decode_entities(html)

    match = RE_BASE_URL.search(html)
    if match:
        return match.group(1)
    else:
        return None

def strip_tags(html, normalize_space=True):
    text = RE_TAG.sub(' ', html)
    if normalize_space:
        return normalize_space_func(text)
    else:
        return text
