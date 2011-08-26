# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
from __future__ import absolute_import
from grab import DataNotFound, GrabError
import re

RE_NUMBER = re.compile(r'\d+')
RE_NUMBER_WITH_SPACES = re.compile(r'\d[\s\d]+', re.U)
RE_SPACE = re.compile(r'\s+', re.U)

class Extension(object):
    export_attributes = ['search', 'search_rex', 'assert_substring', 'assert_rex',
                         'find_number', 'drop_spaces']
        
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
                raise GrabError('The anchor should be bytes string in byte mode')
            else:
                return anchor in self.response.unicode_body()

        if not isinstance(anchor, unicode):
            if byte:
                return anchor in self.response.body
            else:
                raise GrabError('The anchor should be unicode string in non-byte mode')

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
            return anchor.search(self.response.body) or None
        else:
            return anchor.search(self.response.unicode_body()) or None

    def assert_substring(self, anchor, byte=False):
        """
        If `anchor` is not found then raise `DataNotFound` exception.
        """

        if not self.search(anchor, byte=byte): 
            raise DataNotFound('Substring not found: %s' % anchor)

    def assert_rex(self, rex, byte=False):
        """
        If `rex` expression is not found then raise `DataNotFound` exception.
        """

        if not self.search_rex(anchor, byte=byte): 
            raise DataNotFound('Substring not found: %s' % anchor)

    def find_number(self, text, ignore_spaces=False):
        """
        Find the group of digits.

        If `ignore_spaces` is True then search for group of digits which
        could be delimited with spaces.

        If no digits were found raise `DataNotFound` exception.
        """

        if ignore_spaces:
            match = self.drop_spaces(RE_NUMBER_WITH_SPACES.search(text))
        else:
            match = RE_NUMBER.search(text)
        if match:
            return match.group(0)
        else:
            raise DataNotFound

    def drop_spaces(self, text):
        """
        Drop all space-chars in the `text`.
        """

        return RE_SPACE.sub('', value).strip()
