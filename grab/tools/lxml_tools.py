"""
Functions to process content of lxml nodes.
"""
import re

from grab.tools.text import normalize_space as normalize_space_func, find_number
from grab.tools.encoding import smart_str, smart_unicode

from grab.util.py3k_support import *

RE_TAG_START = re.compile(r'<[a-z]')


def get_node_text(node, smart=False, normalize_space=True):
    """
    Extract text content of the `node` and all its descendants.

    In smart mode `get_node_text` insert spaces between <tag><another tag>
    and also ignores content of the script and style tags.

    In non-smart mode this func just return text_content() of node
    with normalized spaces
    """

    # If xpath return a attribute value, it value will be string not a node
    if isinstance(node, basestring):
        if normalize_space:
            node = normalize_space_func(node)
        return node

    if smart:
        value = ' '.join(node.xpath(
            './descendant-or-self::*[name() != "script" and '\
            'name() != "style"]/text()[normalize-space()]'))
    else:
        # If DOM tree was built with lxml.etree.fromstring
        # then tree nodes do not have text_content() method
        try:
            value = node.text_content()
        except AttributeError:
            value = ''.join(node.xpath('.//text()'))
    if normalize_space:
        value = normalize_space_func(value)
    return value


def find_node_number(node, ignore_spaces=False, make_int=True):
    """
    Find number in text content of the `node`.
    """

    text = get_node_text(node)
    return find_number(text, ignore_spaces=ignore_spaces, make_int=make_int)


def truncate_tail(node, xpath):
    """
    Find sub-node by its xpath and remove it and all adjacent nodes following
    after found node.
    """

    subnode = node.xpath(xpath)[0]
    for item in subnode.xpath('following-sibling::*'):
        item.getparent().remove(item)
    subnode.getparent().remove(subnode)


def parse_html(html, encoding='utf-8'):
    """
    Parse html into ElementTree node.
    """
    import lxml.html

    parser = lxml.html.HTMLParser(encoding=encoding)
    return lxml.html.fromstring(html, parser=parser)


def render_html(node, encoding='utf-8', make_unicode=False):
    """
    Render Element node.
    """
    import lxml.html

    if make_unicode or encoding == 'unicode':
        return lxml.html.tostring(node, encoding='utf-8').decode('utf-8')
    else:
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


def clone_node(elem):
    """
    Create clone of Element node.

    The resulted clone is not connected ot original DOM tree.
    """

    return parse_html(render_html(elem))


def disable_links(elem):
    """
    Replace all links with span tags and drop href atrributes.
    """

    for node in elem.xpath('.//a'):
        node.tag = 'span'
        if 'href' in node.attrib:
            del node.attrib['href']


def sanitize_html(html, encoding='utf-8', return_unicode=False):
    html = smart_str(html, encoding=encoding)
    if RE_TAG_START.search(html):
        html = render_html(parse_html(html))
    if return_unicode:
        return html.decode('utf-8')
    else:
        return html


def drop_node(tree, xpath, keep_content=False):
    """
    Find sub-node by its xpath and remove it.
    """

    for node in tree.xpath(xpath):
        parent = node.getparent()
        if keep_content:
            # Find position of node in list of adjacent nodes
            pos = parent.index(node) + 1
            # move all node's childrent to level higher
            for subnode in node:
                parent.insert(pos, subnode)
                pos += 1
            # now replace node with its text
            node_text = (node.text or '') + (node.tail or '')
            replace_rawnode_with_text(node, node_text)
        else:
            replace_rawnode_with_text(node, node.tail or '')


def replace_node_with_text(root, xpath, text):
    for node in root.xpath(xpath):
        new_text = (text + node.tail) if node.tail else text
        replace_rawnode_with_text(node, new_text)


def replace_rawnode_with_text(node, text):
    parent = node.getparent()
    if parent is not None:
        previous = node.getprevious()
        if previous is not None:
            previous.tail = (previous.tail or '') + text
        else:
            parent.text = (parent.text or '') + text
        parent.remove(node)


def clean_html(html, safe_attrs=('src', 'href'),
               input_encoding='unicode',
               output_encoding='unicode',
               **kwargs):
    """
    Fix HTML structure and remove non-allowed attributes from all tags.
    """

    from lxml.html.clean import Cleaner

    # Convert HTML to Unicode
    html = render_html(parse_html(html, encoding=input_encoding), make_unicode=True)

    # Strip some shit with default lxml tools
    cleaner = Cleaner(page_structure=True, **kwargs)
    html = cleaner.clean_html(html)

    # Keep only allowed attributes
    tree = parse_html(html)
    for elem in tree.xpath('./descendant-or-self::*'):
        for key in elem.attrib.keys():
            if safe_attrs:
                if key not in safe_attrs:
                    del elem.attrib[key]

    return render_html(tree, encoding=output_encoding)
