import os
import signal
import sys
import logging
import time

class Watcher(object):
    """this class solves two problems with multithreaded
    programs in Python, (1) a signal might be delivered
    to any thread (which is just a malfeature) and (2) if
    the thread that gets the signal is waiting, the signal
    is ignored (which is a bug).

    The watcher is a concurrent process (not thread) that
    waits for a signal and the process that contains the
    threads.  See Appendix A of The Little Book of Semaphores.
    http://greenteapress.com/semaphores/

    I have only tested this on Linux.  I would expect it to
    work on the Macintosh and not work on Windows.
    """
    
    def __init__(self):
        """ Creates a child thread, which returns.  The parent
            thread waits for a KeyboardInterrupt and then kills
            the child thread.
        """
        self.child = os.fork()
        if self.child == 0:
            return
        else:
            self.watch()

    def watch(self):
        try:
            os.wait()
        except KeyboardInterrupt:
            logging.debug('Watcher process received KeyboardInterrupt')
            logging.debug('Sending SIGUSR2 signal to child process')
            try:
                os.kill(self.child, signal.SIGUSR2)
            except OSError:
                pass
            logging.debug('Waiting 5 seconds before sending SIGKILL')
            time.sleep(5)
            logging.debug('Sending SIGKILL signal to child process')
            try:
                os.kill(self.child, signal.SIGKILL)
            except OSError:
                pass
        sys.exit()


def watch():
    Watcher()
