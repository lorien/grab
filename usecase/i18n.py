# coding: utf-8
import setup_script
from grab import Grab
from urlparse import urlsplit, urlunsplit
import re

RE_NON_ASCII = re.compile(r'[^-.a-zA-Z0-9]')

g = Grab()

url = u'http://почта.рф/'
g.go(url)
print g.response.body
