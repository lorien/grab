"""
This is obsoleted module. Use selection package instead.
"""
from selection.base import SelectorList, RexResultList  # noqa
from selection.backend import PyquerySelector, XpathSelector as XpathSelectorOrigin

from grab.error import warn


class XpathSelector(XpathSelectorOrigin):
    def __init__(self, *args, **kwargs):
        warn('You are using XpathSelector from deprecated `grab.selector` '
             'package. Please, switch to `selection` package.')
        super(XpathSelector, self).__init__(*args, **kwargs)
