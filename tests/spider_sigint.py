# coding: utf-8
"""
Known issues

1) Sometimes the child python processs segfaults :)
Log:
INFO:tornado.access:200 GET / (::1) 10.79ms
ERROR:root:killing children
INFO:tornado.access:200 GET / (::1) 11.25ms
...
ERROR:root:CHILD: 2451
ERROR:root:step-4
before proc-poll-0
INFO:tornado.access:200 GET / (::1) 10.96ms
INFO:tornado.access:200 GET / (::1) 10.67ms
ERROR:root:EXITING WITH CODE 13
Segmentation fault
before proc-poll-1
ERROR:root:step-5
ERROR:root:WTF
Traceback (most recent call last):
  File "/home/lorien/web/grab/test/spider_sigint.py", line 99, in test_sigint
    self.assertEqual(13, ret)
  File "/usr/lib/python2.7/unittest/case.py", line 513, in assertEqual
    assertion_func(first, second, msg=msg)
  File "/usr/lib/python2.7/unittest/case.py", line 506, in _baseAssertEqual
    raise self.failureException(msg)
AssertionError: 13 != 139

2) Sometimes the child python process ignores the SIGINT signal

I have no idea why all these happens. I just need this test "works". What is
why there such many workarounds in the code of the test.
"""

from tests.util import BaseGrabTestCase
from tests.util_sigint import BaseKeyboardInterruptTestCase

SCRIPT_TPL = """
import sys
import logging
import signal
try:
    from grab.spider import Spider, Task
    from grab import Grab
    import os
    import grab
    #logging.error('PATH: ' + grab.__file__)
    #logging.error('PID: ' + str(os.getpid()))

    class TestSpider(Spider):
        def task_generator(self):
            for x in range(100):
                g = Grab(%s)
                g.setup(url="%s")
                yield Task('page', grab=g)

        def task_page(self, grab, task):
            pass

    bot = TestSpider(thread_number=2)
    bot.run()
except KeyboardInterrupt:
    #logging.error('EXITING WITH CODE 13')
    sys.exit(13)
else:
    #logging.error('OK')
    sys.exit(0)
""".lstrip()
# SIGNAL_INT = (signal.CTRL_C_EVENT if platform.system() == 'Windows'
#              else signal.SIGINT)


class SpiderKeyboardInterruptTestCase(BaseKeyboardInterruptTestCase, BaseGrabTestCase):
    script_tpl = SCRIPT_TPL
