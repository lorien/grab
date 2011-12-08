# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
from __future__ import absolute_import
from contextlib import contextmanager
import logging

from ..base import DataNotFound, GrabError, GrabMisuseError
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


    def search_rex(self, rex, byte=False):
        """
        Search the regular expression in response body.

        :param byte: if False then search is performed in `response.unicode_body()`
            else the rex is searched in `response.body`.

        Note: if you use default non-byte mode than do not forget to build your
        regular expression with re.U flag.

        Returns found match or None
        """

        logging.error('This method is deprecated. Use `rex` method instead')
        if byte:
            return rex.search(self.response.body) or None
        else:
            return rex.search(self.response.unicode_body()) or None


    def assert_rex(self, rex, byte=False):
        """
        If `rex` expression is not found then raise `DataNotFound` exception.
        """

        logging.error('This method is deprecated. Use `rex` method instead')
        self.rex(rex, byte=byte)
