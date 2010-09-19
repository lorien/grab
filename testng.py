from grab.grabng import Grab
import logging
import os
import sys

logging.basicConfig(level=logging.DEBUG)
g = Grab()
g.go('http://google.com')
print g.form_fields()
