# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
"""
Interface to leaf: http://pypi.python.org/pypi/leaf/
"""
from __future__ import absolute_import
from grab.response import Response

def monkey():
    '''Usage:
        from grab.ext.leaf import monkey; monkey()
        # and then you can use g.request.leaf
    '''
    from leaf import parse

    def leaf(self):
        if not getattr(self, '_leaf', None):
            self._leaf = parse(self.body, encoding=self.charset)
        return self._leaf

    Response.leaf = property(leaf)


class LeafExtension(object):
    """
    This extension provides ``leaf`` attribute which allows
    you to work with response DOM tree via leaf interface.
    """

    def extra_reset(self):
        self._leaf = None

    @property
    def leaf(self):
        """
        Return body parsed by leaf
        """
        import leaf

        if not self._leaf:
            self._leaf = leaf.parse(self.response.unicode_body(),
                    encoding=self.charset)
        return self._leaf
