# Copyright: 2013, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: MIT
from __future__ import absolute_import
import weakref

from grab.selector import KitSelector

class KitInterface(object):
    def __init__(self, grab):
        self.grab = weakref.proxy(grab)

    def select(self, *args, **kwargs):
        qt_doc = self.grab.transport.kit.page.mainFrame().documentElement()
        return KitSelector(qt_doc).select(*args, **kwargs)


class KitExtension(object):
    __slots__ = ()
    # SLOTS: _kit

    def extra_reset(self):
        self._kit = None

    @property
    def kit(self):
        """
        Return KitInterface object which provides some
        methods to communicate with Kit transport related functions.
        """
        
        if not self._kit:
            self._kit = KitInterface(self)
        return self._kit
