"""
This is obsoleted module. Use selection package instead.
"""

from selection.selector import BaseSelector
from selection.selector_list import SelectorList, RexResultList
from selection.backend.xpath import XpathSelector as XpathSelectorOrigin
from selection.backend.text import TextSelector
from selection.backend.pyquery import PyquerySelector
from grab.error import warn


class XpathSelector(XpathSelectorOrigin):
    def select(self, *args, **kwargs):
        warn('You are using XpathSelector from deprecated `grab.selector` package. '
             'Please, switch to `selection` package.')

        return super(XpathSelector, self).select(*args, **kwargs)
