#!/usr/bin/env python
from grab.tools.tinyurl import MODULES, get_tiny_url
import logging
from grab.tools.watch import watch

watch()
logging.basicConfig(level=logging.DEBUG)
TEST_URL = 'http://google.com'

for name, module in MODULES.items():
    print 'Service:', module.name
    try:
        print get_tiny_url(TEST_URL, service=name)
    except Exception, ex:
        print ex
