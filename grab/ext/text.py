# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
from __future__ import absolute_import
from contextlib import contextmanager
import logging

from ..error import DataNotFound, GrabError, GrabMisuseError
from ..tools.text import normalize_space
from ..tools.html import decode_entities

class TextExtension(object):
    def search(self, anchor, byte=False):
        """
        Search the substring in response body.

        :param anchor: string to search
        :param byte: if False then `anchor` should be the
            unicode string, and search will be performed in `response.unicode_body()`
            else `anchor` should be the byte-string and
            search will be performed in `resonse.body`
        
        If substring is found return True else False.
        """

        if isinstance(anchor, unicode):
            if byte:
                raise GrabMisuseError('The anchor should be bytes string in byte mode')
            else:
                return anchor in self.response.unicode_body()

        if not isinstance(anchor, unicode):
            if byte:
                return anchor in self.response.body
            else:
                raise GrabMisuseError('The anchor should be byte string in non-byte mode')

    def assert_substring(self, anchor, byte=False):
        """
        If `anchor` is not found then raise `DataNotFound` exception.
        """

        if not self.search(anchor, byte=byte): 
            raise DataNotFound('Substring not found: %s' % anchor)


    def assert_substrings(self, anchors, byte=False):
        """
        If no `anchors` were found then raise `DataNotFound` exception.
        """

        found = False
        for anchor in anchors:
            if self.search(anchor, byte=byte): 
                found = True
                break
        if not found:
            raise DataNotFound('Substrings not found: %s' % ', '.join(anchors))
