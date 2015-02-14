# Copyright: 2012, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
import logging
from hashlib import sha1
from time import mktime
from datetime import datetime
import feedparser
from lxml.html.clean import clean_html

from grab.tools.lxml_tools import truncate_html
from grab.tools.html import strip_tags
from grab.tools.text import remove_bom
from grab.error import DataNotFound, GrabMisuseError

log = logging.getLogger('grab.tools.feed')


def parse_entry_date(entry):
    date_fields = ('published', 'created', 'updated', 'modified')

    for key in date_fields:
        value = getattr(entry, '%s_parsed' % key, None)
        if value:
            return datetime.fromtimestamp(mktime(value))

    raise Exception('Could not parse date of entry %s' % entry.link)


def parse_entry_tags(entry):
    """Return a list of tag objects of the entry"""

    tags = set()

    for tag in entry.get('tags', []):
        term = tag.get('label') or tag.get('term') or ''
        for item in term.split(','):
            item = item.strip().lower()
            if item:
                tags.add(item)

    return list(tags)


def parse_entry_content(entry):

    body = ''
    if hasattr(entry, 'content'):
        mapping = dict((x.type, x.value) for x in entry.content)
        if 'text/html' in mapping:
            body = mapping['text/html']
        elif 'application/xhtml+xml' in mapping:
            body = mapping['application/xhtml+xml']
        else:
            body = list(mapping.values())[0]

    if hasattr(entry, 'summary') and len(entry.summary) > len(body):
        body = entry.summary

    if hasattr(entry, 'description') and len(entry.description) > len(body):
        body = entry.description

    return body


def parse_entry_teaser(entry, size):
    content = truncate_html(parse_entry_content(entry), size)
    return content


def build_entry_content(entry, teaser=False, teaser_size=None):
    content = clean_html(parse_entry_content(entry))
    if teaser:
        content = truncate_html(content, teaser_size)
    return content


def parse_feed(grab, teaser_size=1000):
    """
    Extract details of feed fetched with Grab.

    Returns dict with keys:
    * feed
    * entries
    """

    # BOM removing is required because without it
    # sometimes feedparser just raise SegmentationFault o_O
    feed = feedparser.parse(remove_bom(grab.response.body))

    entries = []
    for entry in feed.entries:
        try:
            entries.append(parse_entry(entry, feed, teaser_size=teaser_size))
        except Exception as ex:
            log.error('Entry parsing error', exc_info=ex)
    
    return {'feed': feed, 'entries': entries}


def parse_entry(entry, feed, teaser_size):
    details = {
        'url': entry.link,
        'title': strip_tags(entry.title),
        'content': build_entry_content(entry),
        'teaser': build_entry_content(entry, teaser=True,
                                      teaser_size=teaser_size),
        'date': parse_entry_date(entry),
        'tags': parse_entry_tags(entry),
    }

    guid_token = (entry.get('id') or entry.link).encode('utf-8')
    details['guid'] = sha1(guid_token).hexdigest()

    if not details['date']:
        raise Exception('Entry %s does not has publication date' % entry.link)

    return details
