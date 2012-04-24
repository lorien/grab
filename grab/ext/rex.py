# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
from __future__ import absolute_import
from contextlib import contextmanager

from ..error import DataNotFound, GrabError, GrabMisuseError
from ..tools.text import normalize_space
from ..tools.html import decode_entities
from ..tools.rex import rex_cache

NULL = object()

class RegexpExtension(object):
    def rex_text(self, regexp, flags=0, byte=False, default=NULL):
        """
        Search regular expression in response body and return content of first
        matching group.

        :param byte: if False then search is performed in `response.unicode_body()`
            else the rex is searched in `response.body`.
        """

        try:
            match = self.rex(regexp, flags=flags, byte=byte)
        except DataNotFound:
            if default is NULL:
                raise DataNotFound('Regexp not found')
            else:
                return default
        else:
            return normalize_space(decode_entities(match.group(1)))

    def rex(self, regexp, flags=0, byte=False, default=NULL):
        """
        Search the regular expression in response body.

        :param byte: if False then search is performed in `response.unicode_body()`
            else the rex is searched in `response.body`.

        Note: if you use default non-byte mode than do not forget to build your
        regular expression with re.U flag.

        Return found match object or None

        """

        regexp = self.normalize_regexp(regexp, flags)
        if byte:
            match =  regexp.search(self.response.body)
        else:
            match = regexp.search(self.response.unicode_body())
        if match:
            return match
        else:
            if default is NULL:
                rstr = regexp#regexp.source if regexp.hasattr('source') else regexp
                raise DataNotFound('Could not find regexp: %s' % regexp)
            else:
                return default

    def normalize_regexp(self, regexp, flags=0):
        """
        Accept string or compiled regular expression object.

        Compile string into regular expression object.
        """

        if isinstance(regexp, basestring):
            return rex_cache(regexp, flags)
        else:
            return regexp

    def assert_rex(self, rex, byte=False):
        """
        If `rex` expression is not found then raise `DataNotFound` exception.
        """

        self.rex(rex, byte=byte)
