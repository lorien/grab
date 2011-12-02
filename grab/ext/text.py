# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
from __future__ import absolute_import
from contextlib import contextmanager

from ..base import DataNotFound, GrabError, GrabMisuseError
from ..tools.text import normalize_space
from ..tools.html import decode_entities
from ..tools.rex import rex_cache

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

    def search_rex(self, rex, byte=False):
        """
        Search the regular expression in response body.

        :param byte: if False then search is performed in `response.unicode_body()`
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


    def rex_text(self, rex, flags=0):
        rex = self.normalize_regexp(rex, flags)
        try:
            return normalize_space(decode_entities(self.search_rex(rex).group(1)))
        except AttributeError:
            raise DataNotFound('Regexp not found')

    @contextmanager
    def rex(self, regexp, flags=0):
        """
        Search regexp in response body.

        Return found match or None
        """

        regexp = self.normalize_regexp(regexp, flags)
        match = regexp.search(self.response.unicode_body())
        if match:
            yield match.group(1)
        else:
            yield None

    def extract_rex_list(rex, flags=0):
        """
        Return found matches.
        """

        rex = self.normalize_regexp(rex, flags)
        return rex.findall(self.response.unicode_body())

    def normalize_regexp(self, regexp, flags=0):
        """
        Accept string or compiled regular expression object.

        Compile string into regular expression object.
        """

        if isinstance(regexp, basestring):
            return rex_cache(regexp, flags)
        else:
            return regexp
