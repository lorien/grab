"""
Functions to process content of lxml nodes.
"""
from text import normalize_space as normalize_space_func, find_number

def get_node_text(node, smart=False, normalize_space=True):
    """
    Extract text content of the `node` and all its descendants.

    In smart mode `get_node_text` insert spaces between <tag><another tag>
    and also ignores content of the script and style tags.

    In non-smart mode this func just return text_content() of node
    with normalized spaces
    """

    if smart:
        value = ' '.join(node.xpath(
            './descendant-or-self::*[name() != "script" and '\
            'name() != "style"]/text()[normalize-space()]'))
    else:
        value = node.text_content()
    if normalize_space:
        value = normalize_space_func(value)
    return value

def find_node_number(node, ignore_spaces=False):
    """
    Find number in text content of the `node`.
    """

    return find_number(get_node_text(node), ignore_spaces=ignore_spaces)
