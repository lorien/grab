# Copyright: 2013, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: MIT
from __future__ import absolute_import
import weakref

from grab.selector import XpathSelector
#from grab.tools.structured import TreeInterface

class DocInterface(object):
    def __init__(self, grab):
        self.grab = weakref.proxy(grab)

    def select(self, *args, **kwargs):
        return XpathSelector(self.grab.tree).select(*args, **kwargs)

    #def structure(self, *args, **kwargs):
        #return TreeInterface(self.grab.tree).structured_xpath(*args, **kwargs)


class DocExtension(object):
    __slots__ = ()
    # SLOTS: _doc

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
