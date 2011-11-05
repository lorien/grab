"""
Provide functions for check if file is locked.
"""

from fcntl import flock, LOCK_EX, LOCK_NB
import os.path
import sys
import logging
import os

fh = None

def set_lock(fname):
    """
    Try to lock file and write PID.
    
    Return the status of operation.
    """

    global fh
    fh = open(fname, 'w')
    try:
        flock(fh.fileno(), LOCK_EX | LOCK_NB)
    except Exception, ex:
        return False
    else:
        fh.write(str(os.getpid()))
        fh.flush()
    return True


def assert_lock(fname):
    """
    If file is locked then terminate program else lock file.
    """

    logging.debug('Trying to lock: %s' % fname)
    if not set_lock(fname):
        logging.error(u'%s is already locked. Terminating.' % fname)
        sys.exit()
