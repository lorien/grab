import logging
import os
import sys
from grab import Grab

logging.basicConfig(level=logging.DEBUG)
g = Grab(['grab.ext.urllib2', 'grab.ext.lxml'])
g.go('http://google.com')
print g.xpath('//title')[0].text
