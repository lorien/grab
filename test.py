# coding: utf-8
import csv
import logging

from grab.spider import Spider, Task
from grab import Grab

g = Grab()
g.go('http://drlz.kiev.ua/ibp/ddsite.nsf/all/shlist?opendocument')
g.setup(charset='cp1251')
g.set_input('title', u'анальг')
g.submit()
g.response.save('/tmp/x.html')
