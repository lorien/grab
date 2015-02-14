import os

from grab.util.py3k_support import *

SCALE = {'kB': 1024.0, 'mB': 1024.0 * 1024.0,
         'KB': 1024.0, 'MB': 1024.0 * 1024.0}


def memory_usage(since=0, render=True, pid=None):
    """
    Return resident memory usage in bytes.
    """

    if pid is None:
        pid = os.getpid()

    proc_status = '/proc/%d/status' % pid
    try:
        status = open(proc_status).read()
    except:
        return 0
    else:
        line = [x for x in status.splitlines() if 'VmRSS:' in x][0]
        items = line.split('VmRSS:')[1].strip().split(' ')
        mem = float(items[0]) * SCALE[items[1]] - since
        if render:
            metrics = ['b', 'Kb', 'Mb', 'Gb']
            metric = metrics.pop(0)
            for x in xrange(3):
                if mem > 1024:
                    mem /= 1024.0
                    metric = metrics.pop(0)
            return '%s %s' % (str(round(mem, 2)), metric)
        else:
            return mem
