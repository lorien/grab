"""
Provide functions for check if file is locked.
"""

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

    if os.name == 'nt':
        # Code for NT systems got from: http://code.activestate.com/recipes/65203/
        
        import win32con
        import win32file
        import pywintypes
        
        LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
        LOCK_SH = 0 # the default
        LOCK_NB = win32con.LOCKFILE_FAIL_IMMEDIATELY
        
        # is there any reason not to reuse the following structure?
        __overlapped = pywintypes.OVERLAPPED()
        
        hfile = win32file._get_osfhandle(fh.fileno())
        try:
            win32file.LockFileEx(hfile, LOCK_EX | LOCK_NB, 0, -0x10000, __overlapped)
        except pywintypes.error, exc_value:
            # error: (33, 'LockFileEx', 'The process cannot access 
            # the file because another process has locked a portion
            # of the file.')
            if exc_value[0] == 33:
                return False
    else:
        from fcntl import flock, LOCK_EX, LOCK_NB
        try:
            flock(fh.fileno(), LOCK_EX | LOCK_NB)
        except Exception, ex:
            return False
    
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
