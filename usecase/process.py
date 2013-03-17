import setup_script
from multiprocessing import Process, Event
import os
import time
import logging

def foo(sleep_time, shutdown_event):
    logging.error('Error message from child process')
    while True:
        print 'Sleeping for %s sec.' % sleep_time
        time.sleep(sleep_time)
        print 'Checking shutdown event'
        if shutdown_event.is_set():
            print 'Shutdown event is on'
            break
    print 'pid', os.getpid()


def main():
    print 'Parent pid:', os.getpid()
    shutdown_event = Event()
    p = Process(target=foo, args=[1, shutdown_event])
    p.start()
    time.sleep(3)
    shutdown_event.set()
    print 'Main func done'


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.addHandler(logging.FileHandler('var/log.txt', 'w'))
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)
    main()
