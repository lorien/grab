import re
from .text import normalize_space as normalize_space_func, find_number

def find_content_blocks(tree, min_length=None):
    """
    Iterate over content blocks (russian version)
    """
    from lxml.html import tostring
    from lxml.etree import strip_tags, strip_elements, Comment

    # Completely remove content of following tags
    nondata_tags = ['head', 'style', 'script', Comment]
    strip_elements(tree, *nondata_tags)

    # Remove links
    strip_elements(tree, 'a')

    # Drop inlines tags
    inline_tags = ('br', 'hr', 'p', 'b', 'i', 'strong', 'em', 'a',
                   'span', 'font')
    strip_tags(tree, *inline_tags)

    # Cut of images
    media_tags = ('img',)
    strip_tags(tree, *media_tags)

    body = tostring(tree, encoding='utf-8').decode('utf-8')

    # Normalize spaces
    body = normalize_space_func(body)

    # Find text blocks
    block_rex = re.compile(r'[^<>]+')

    blocks = []
    for match in block_rex.finditer(body):
        block = match.group(0)
        if len(block) > 100:
            ratio = _trash_ratio(block)
            if ratio < 0.05:
                block = block.strip()
                if min_length is None or len(block) >= min_length:
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
