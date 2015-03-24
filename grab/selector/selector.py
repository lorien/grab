"""
This is obsoleted module. Use selection package instead.
"""

from selection.selector_list import SelectorList, RexResultList  # noqa
from selection.backend.xpath import XpathSelector as XpathSelectorOrigin
from selection.backend.pyquery import PyquerySelector  # noqa
from grab.error import warn


class XpathSelector(XpathSelectorOrigin):
    def __init__(self, *args, **kwargs):
        warn('You are using XpathSelector from deprecated `grab.selector` '
             'package. Please, switch to `selection` package.')
        super(XpathSelector, self).__init__(*args, **kwargs)
