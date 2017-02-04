# coding: utf-8
import signal
import os
import time
from subprocess import Popen
from psutil import Process
import platform
import logging
import atexit

from test.util import BaseGrabTestCase
from test.util import build_grab, temp_file, only_grab_transport
from test.util import skip_test_if

def shutdown():
    print('SHUTDOWN')

atexit.register(shutdown)

SCRIPT_TPL = '''
import sys
from grab import Grab
import logging
import os
import grab
logging.error('PATH: ' + grab.__file__)
logging.error('PID: ' + str(os.getpid()))
g = Grab(%s)
try:
    for x in range(100):
        g.go('%s')
except KeyboardInterrupt:
    logging.error('EXITING WITH CODE 13')
    sys.exit(13)
else:
    logging.error('OK')
    sys.exit(0)
'''.lstrip()
SIGNAL_INT = (signal.CTRL_C_EVENT if platform.system() == 'Windows'
              else signal.SIGINT)


class TestKeyboardInterrupt(BaseGrabTestCase):
    """
    I have no idea how to run this test on windows.
    Then I send CTRL_C_EVENT to process opened with Popen
    the whole testing process is hanged.
    """
    def setUp(self):
        self.server.reset()

    @skip_test_if(lambda: platform.system() == 'Windows', 'windows platform')
    @only_grab_transport('pycurl')
    def test_sigint(self):
        logging.error('step-0')
        self.server.response['sleep'] = 0.01
        with temp_file() as path:
            with open(path, 'w') as out:
                out.write(SCRIPT_TPL % ('', self.server.get_url()))
            for x in range(1):
                logging.error('step-1')
                proc = Popen('python %s' % path, shell=True)
                logging.error('step-2')
                parent = Process(proc.pid)
                logging.error('step-3')
                time.sleep(0.5)
                logging.error('killing children')
                for child in parent.children():
                    logging.error('CHILD: %s' % child.pid)
                    child.send_signal(SIGNAL_INT)
                if platform.system() == 'Darwin': 
                    # On OSX the Popen(shell=True) spawns only
                    # one process, no child
                    logging.error('Killing parent')
                    logging.error('PARENT: %s' % parent.pid)
                    parent.send_signal(SIGNAL_INT)
                logging.error('step-4')
                try:
                    for x in range(20):
                        print('before proc-poll-%d' % x)
                        ret = proc.poll()
                        if ret is not None:
                            break
                        time.sleep(0.1)
                    else:
                        raise Exception('Child process did not return')
                    logging.error('step-5')
                    self.assertEqual(13, ret)
                except Exception as ex:
                    logging.error('WTF', exc_info=ex)
                    raise
                finally:
                    logging.error('FINAL')

    @skip_test_if(lambda: platform.system() == 'Windows', 'windows platform')
    @only_grab_transport('pycurl')
    def test_sigint_nobody(self):
        logging.error('step-0')
        self.server.response['sleep'] = 0.01
        with temp_file() as path:
            with open(path, 'w') as out:
                out.write(SCRIPT_TPL % ('nobody=True', self.server.get_url()))
            for x in range(10):
                logging.error('step-1')
                proc = Popen('python %s' % path, shell=True)
                logging.error('step-2')
                parent = Process(proc.pid)
                logging.error('step-3')
                time.sleep(0.5)
                logging.error('killing children')
                for child in parent.children():
                    logging.error('CHILD: %s' % child.pid)
                    child.send_signal(SIGNAL_INT)
                if platform.system() == 'Darwin': 
                    # On OSX the Popen(shell=True) spawns only
                    # one process, no child
                    logging.error('Killing parent')
                    logging.error('PARENT: %s' % parent.pid)
                    parent.send_signal(SIGNAL_INT)
                logging.error('step-4')
                for x in range(20):
                    ret = proc.poll()
                    if ret is not None:
                        break
                    time.sleep(0.1)
                else:
                    raise Exception('Child process did not return')
                logging.error('step-5')
                self.assertEqual(13, ret)
