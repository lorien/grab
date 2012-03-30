"""
Functions to process content of lxml nodes.
"""
from StringIO import StringIO

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


def truncate_tail(node, xpath):
    """
    Find sub-node by its xpath and remove it and all adjacent nodes following
    after found node.
    """

    subnode = node.xpath(xpath)[0]
    for item in subnode.xpath('following-sibling::*'):
        item.getparent().remove(item)
    subnode.getparent().remove(subnode)


def drop_node(node, xpath):
    """
    Find sub-node by its xpath and remove it.
    """

    for item in node.xpath(xpath):
        item.getparent().remove(item)


def parse_html(html, encoding='utf-8'):
    """
    Parse html into ElementTree node.
    """
    import lxml.html

    parser = lxml.html.HTMLParser(encoding=encoding)
    return lxml.html.fromstring(html, parser=parser)


def render_html(node, encoding='utf-8'):
    import lxml.html

    return lxml.html.tostring(node, encoding=encoding)


def truncate_html(html, limit, encoding='utf-8'):
    """
    Truncate html data to specified length and then fix broken tags.
    """

    if not isinstance(html, unicode):
        html = html.decode(encoding)
    truncated_html = html[:limit]
    elem = parse_html(truncated_html, encoding=encoding)
    fixed_html = render_html(elem, encoding=encoding)
    return fixed_html
