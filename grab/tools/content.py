import re
from copy import deepcopy

from grab.tools.text import normalize_space, find_number

def find_content_blocks(tree, min_length=None):
    """
    Iterate over content blocks (russian version)
    """
    from lxml.html import tostring
    from lxml.etree import strip_tags, strip_elements, Comment

    # First, make a copy of DOM-tree to not harm external code
    tree = deepcopy(tree)

    # Completely remove content of following tags
    nondata_tags = ['head', 'style', 'script']
    strip_elements(tree, *nondata_tags)

    # Remove comment nodes (keep tail text)
    strip_tags(tree, Comment)

    # Remove links
    strip_tags(tree, 'a')

    # Drop inline tags
    inline_tags = ('br', 'hr', 'p', 'b', 'i', 'strong', 'em', 'a',
                   'span', 'font')
    strip_tags(tree, *inline_tags)

    # Drop media tags
    media_tags = ('img',)
    strip_tags(tree, *media_tags)

    body = tostring(tree, encoding='utf-8').decode('utf-8')

    # Normalize spaces
    body = normalize_space(body)

    # Remove ALL chars from tags
    re_tag = re.compile(r'<[^>]+>')
    body = re_tag.sub(r'<>', body)

    #with open('/tmp/log.html', 'w') as out:
        #out.write(body.encode('utf-8'))
    #return

    # Find text blocks
    block_rex = re.compile(r'[^<>]+')

    blocks = []
    for match in block_rex.finditer(body):
        block = match.group(0)
        if min_length is None or len(block) >= min_length:
            ratio = _trash_ratio(block)
            if ratio < 0.05:
                words = block.split()
                if not any(len(x) > 50 for x in words):
                    blocks.append(block)
    return blocks


def _trash_ratio(text):
    """
    Return ratio of non-common symbols.
    """

    trash_count = 0
    for char in text:
        if char in list(u'.\'"+-!?()[]{}*+@#$%^&_=|/\\'):
            trash_count += 1
    return trash_count / float(len(text))
