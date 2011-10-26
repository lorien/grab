# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
"""
Deprecated extension. Maybe it does not work.
"""
import re
from BeautifulSoup import BeautifulSoup

SCRIPT_TAG = re.compile(r'(<script[^>]*>).+?(</script>)', re.I|re.S)

class Extendsion(object):
    def extra_reset(self):
        self._soup = None

    #def extra_default_config(self):
        #return {
            #'soup_remove_scripts': True,
        #}

    @property
    def soup(self):
        if not self._soup:
            # Do some magick to make BeautifulSoup happy
            #if False:#self.config['soup_remove_scripts']:
                #data = SCRIPT_TAG.sub(r'\1\2', self.response.body)
            #else:
            data = self.response.body
            self._soup = BeautifulSoup(data)
        return self._soup
