import six

from grab.util.text import normalize_space as normalize_space_func


def get_node_text(node, smart=False, normalize_space=True):
    """
    Extract text content of the `node` and all its descendants.

    In smart mode `get_node_text` insert spaces between <tag><another tag>
    and also ignores content of the script and style tags.

    In non-smart mode this func just return text_content() of node
    with normalized spaces
    """

    # If xpath return a attribute value, it value will be string not a node
    if isinstance(node, six.string_types):
        if normalize_space:
            node = normalize_space_func(node)
        return node

    if smart:
        value = " ".join(
            node.xpath(
                './descendant-or-self::*[name() != "script" and '
                'name() != "style"]/text()[normalize-space()]'
            )
        )
    else:
        # If DOM tree was built with lxml.etree.fromstring
        # then tree nodes do not have text_content() method
        try:
            value = node.text_content()
        except AttributeError:
            value = "".join(node.xpath(".//text()"))
    if normalize_space:
        value = normalize_space_func(value)
    return value
