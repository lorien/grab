# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
from __future__ import absolute_import

from ..base import DataNotFound, GrabError, GrabMisuseError
from ..tools import text as text_tools

class TextExtension(object):
    def search(self, anchor, byte=False):
        """
        Search the substring in response body.

        If `byte` argument is False, then `anchor` should be the
        unicode string, and search will be performed in `response.unicode_body()`
        If `byte` argument is True, then `anchor` should be the
        bytestring and search will be performed in `resonse.body`
        
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

    def search_rex(self, rex, byte=False):
        """
        Search the regular expression in response body.

        If `byte` arguments is False then search is performed in `response.unicode_body()`
        else the rex is searched in `response.body`.

        Note: if you use default non-byte mode than do not forget to build your
        regular expression with re.U flag.

        Returns found match or None
        """

        if byte:
            return rex.search(self.response.body) or None
        else:
            return rex.search(self.response.unicode_body()) or None

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

    def assert_rex(self, rex, byte=False):
        """
        If `rex` expression is not found then raise `DataNotFound` exception.
        """

        if not self.search_rex(rex, byte=byte): 
            raise DataNotFound('Regexp not found')

    def find_number(self, text, ignore_spaces=False):
        """
        Find the number in the `text`.

        :param text: unicode or byte-string text
        :param ignore_spacess: if True then groups of digits delimited
            by spaces are considered as one number
        :raises: :class:`DataNotFound` if number was not found.
        """

        return text_tools.find_number(text, ignore_spaces=ignore_spaces)

    def drop_space(self, text):
        """
        Drop all space-chars in the `text`.
        """

        return text_tools.drop_space(text)

    def normalize_space(self, text):
        """
        Replace multiple adjacent space-chars with one space char.

        Also drop leading and trailing space-chars.
        """

        return text_tools.normalize_space(text)
