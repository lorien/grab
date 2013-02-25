# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
from __future__ import absolute_import
from ..selector import Selector

class DocExtension(object):
    def extra_reset(self):
        self._doc = None

    @property
    def doc(self):
        """
        Return Selector object bined to the `self.tree`
        """
        
        return Selector(self.tree)
