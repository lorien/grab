# coding: utf-8
from tests.util import BaseGrabTestCase
from tests.spider_sigint import BaseKeyboardInterruptTestCase

SCRIPT_TPL = '''
import sys
import logging
try:
    from grab import Grab
    import os
    import grab
    #logging.error('PATH: ' + grab.__file__)
    #logging.error('PID: ' + str(os.getpid()))
    g = Grab(%s)
    for x in range(200):
        g.go('%s')
except KeyboardInterrupt:
    #logging.error('EXITING WITH CODE 13')
    sys.exit(13)
else:
    #logging.error('NO SIGINT')
    sys.exit(0)
'''.lstrip()


class GrabKeyboardInterruptTestCase(BaseKeyboardInterruptTestCase,
                                    BaseGrabTestCase):
    script_tpl = SCRIPT_TPL
