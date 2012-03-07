"""
Functions to process content of lxml nodes.
"""
from text import normalize_space, find_number

def get_node_text(node, smart=True):
    """
    Extract text content of the `node` and all its descendants.

    In smart mode `get_node_text` insert spaces between <tag><another tag>
    and also ignores content of the script and style tags.

    In non-smart mode this func just return text_content() of node
    with normalized spaces
    """

    if smart:
        return normalize_space(' '.join(node.xpath(
            './descendant-or-self::*[name() != "script" and '\
            'name() != "style"]/text()[normalize-space()]')))
    else:
        return normalize_space(node.text_content())

def find_node_number(node, ignore_spaces=False):
    """
    Find number in text content of the `node`.
    """

    return find_number(get_node_text(node), ignore_spaces=ignore_spaces)
