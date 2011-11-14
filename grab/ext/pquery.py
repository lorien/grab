# Copyright: 2011, Alexander Bondarenko
# Author: Alexander Bondarenko (http://aenor.ru)
# License: BSD
from pyquery import PyQuery

class Extension(object):
    def extra_reset(self):
        self._pyquery = None

    @property
    def pyquery(self):
        if not self._pyquery:
            self._pyquery = PyQuery(self.response.body)
        return self._pyquery
