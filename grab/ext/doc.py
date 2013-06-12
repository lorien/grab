# Copyright: 2013, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: MIT
from __future__ import absolute_import
from grab.selector import XpathSelector

class DocInterface(object):
    def __init__(self, grab):
        self.grab = grab

    def select(self, *args, **kwargs):
        return XpathSelector(self.grab.tree).select(*args, **kwargs)


class DocExtension(object):
    def extra_reset(self):
        self._doc = None

    @property
    def doc(self):
        """
        Return DocInterface object which provides some
        shortcuts for faster access to Selector functions.
        """
        
        if not self._doc:
            self._doc = DocInterface(self)
        return self._doc
